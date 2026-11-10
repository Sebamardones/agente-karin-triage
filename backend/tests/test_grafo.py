"""Integración sin red, con SQLite temporal y respuestas sintéticas."""

import json
from pathlib import Path

import anthropic
import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from karin_triage.agent.grafo import construir_grafo, procesar_caso
from karin_triage.agent.nodos import Contexto
from karin_triage.models.salidas_llm import HechosExtraidos, PropuestaClasificacion
from karin_triage.models.tablas import (
    Base,
    Denuncia,
    EventoAuditoria,
    Preclasificacion,
    verificar_cadena,
)
from karin_triage.services.llm import PresupuestoAgotado, RespuestaLLM

CASOS = {c["id"]: c for linea in
         (Path(__file__).resolve().parents[2] / "golden_set/denuncias.jsonl")
         .read_text(encoding="utf-8").splitlines() if (c := json.loads(linea))}


@pytest.fixture
def sesion(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path / 'grafo.db'}")
    Base.metadata.create_all(motor)
    with Session(motor) as s:
        yield s
    motor.dispose()


class ModeloFalso:
    def __init__(self, *, sexual=False, invalidas=0, refusal_en=None, presupuesto_en=None,
                 error_en=None):
        self.sexual = sexual
        self.error_en = error_en
        self.invalidas = invalidas
        self.refusal_en = refusal_en
        self.presupuesto_en = presupuesto_en
        self.llamadas = []
        self.tipificaciones = 0

    def __call__(self, **kw):
        self.llamadas.append(kw)
        n = len(self.llamadas)
        if self.presupuesto_en == n:
            raise PresupuestoAgotado
        if self.error_en == n:
            raise self.error
        refusal = self.refusal_en == n
        texto = kw["contenido_usuario"].split("<denuncia>\n", 1)[1].split("\n</denuncia>")[0]
        citas = [{"texto_literal": texto, "fuente": "denuncia"}]
        if kw["formato"] is HechosExtraidos:
            datos = HechosExtraidos(
                relacion_laboral_declarada=True, empleador_sector="PRIVADO",
                conductas_descritas=[], reiteracion="REITERADA", rol_persona_denunciada="PAR",
                indicios_riesgo_inmediato=[], efectos_declarados=[], citas=citas,
            )
        else:
            self.tipificaciones += 1
            if self.tipificaciones <= self.invalidas:
                citas[0]["texto_literal"] = "CITA INVENTADA QUE NO EXISTE"
            datos = PropuestaClasificacion(
                informacion_suficiente=True,
                decision="DERIVA_MEDIACION" if self.sexual else "PROCEDE_INVESTIGACION",
                tipo_conducta=["ACOSO_SEXUAL" if self.sexual else "ACOSO_LABORAL"],
                vulneracion_ddff=False, motivo_descarte=None, urgencia_resguardo=False,
                confianza=0.95, justificacion="Propuesta para revisión humana.",
                citas=citas, supuestos=[],
            )
        return RespuestaLLM(None if refusal else datos, refusal,
                            "refusal" if refusal else "end_turn", 100, 20, 50, 0.001)


def ejecutar(sesion, caso="G-01", modelo=None):
    modelo = modelo or ModeloFalso()
    estado = construir_grafo(Contexto(sesion, modelo)).invoke({"entrada": CASOS[caso]["entrada"]})
    fila = sesion.scalar(select(Preclasificacion))
    assert fila.denuncia_id == estado["denuncia_id"]
    assert sesion.get(Denuncia, fila.denuncia_id).estado == "PENDIENTE_REVISION_HUMANA"
    return estado, fila, modelo


def test_01_municipal(sesion):
    _, fila, modelo = ejecutar(sesion, "G-04")
    assert fila.estado_auxiliar == "DERIVAR_OTRA_INSTITUCION"
    assert "RD-02" in fila.reglas_aplicadas
    assert not modelo.llamadas
    assert fila.costo_usd == 0


def test_02_sin_relato(sesion):
    _, fila, modelo = ejecutar(sesion, "G-05")
    assert fila.estado_auxiliar == "REQUIERE_ANTECEDENTES"
    assert "RD-01" in fila.reglas_aplicadas
    assert not modelo.llamadas


def test_03_propuesta_valida(sesion):
    estado, fila, modelo = ejecutar(sesion)
    assert fila.decision == "PROCEDE_INVESTIGACION"
    assert fila.prioridad == 3
    assert fila.tokens_entrada == 200 and fila.tokens_salida == 40
    assert fila.cache_read_tokens == 100 and fila.costo_usd == 0.002
    assert estado["llamadas_llm"] == len(modelo.llamadas) == 2
    assert fila.version_pipeline.startswith("tipificar_v3+reglas2+")
    assert modelo.llamadas[0]["effort"] == "low"
    assert modelo.llamadas[1]["effort"] == "medium"
    assert "<dictamenes>\n</dictamenes>" in modelo.llamadas[1]["contenido_usuario"]


def test_04_sexual_nunca_mediacion(sesion):
    _, fila, _ = ejecutar(sesion, "G-02", ModeloFalso(sexual=True))
    assert fila.decision == "PROCEDE_INVESTIGACION"
    assert "RD-10" in fila.reglas_aplicadas
    assert fila.urgencia_resguardo and fila.prioridad == 0


def test_05_pii_residual(sesion, monkeypatch):
    monkeypatch.setattr("karin_triage.agent.nodos.detectar_pii_residual", lambda _: ["EMAIL"])
    _, fila, modelo = ejecutar(sesion)
    assert "PII_RESIDUAL" in fila.marcas_pipeline and fila.prioridad == 0
    assert "RD-06" in fila.reglas_aplicadas
    assert not modelo.llamadas
    assert fila.decision is None


def test_06_refusal(sesion):
    _, fila, _ = ejecutar(sesion, modelo=ModeloFalso(refusal_en=1))
    assert fila.decision is None and fila.prioridad == 0
    assert "LLM_REFUSAL" in fila.marcas_pipeline
    assert "RD-16" in fila.reglas_aplicadas


def test_07_presupuesto(sesion):
    _, fila, _ = ejecutar(sesion, modelo=ModeloFalso(presupuesto_en=1))
    assert fila.decision is None and fila.prioridad == 0
    assert "PRESUPUESTO_AGOTADO" in fila.marcas_pipeline


def _error_proveedor(codigo):
    request = httpx.Request("POST", "https://example.invalid")
    if codigo is None:
        return anthropic.APIConnectionError(request=request)
    return anthropic.APIStatusError(
        "sintetico", response=httpx.Response(codigo, request=request), body=None)


@pytest.mark.parametrize("codigo", [400, 429, 500, None])
@pytest.mark.parametrize("error_en", [1, 2])
def test_07b_error_del_proveedor_va_a_cola_manual(sesion, codigo, error_en):
    """Regresión: un rechazo del proveedor (p. ej. límite de gasto de la consola)
    hacía fallar el grafo y el caso no se guardaba. Ahora queda en la cola humana."""
    modelo = ModeloFalso(error_en=error_en)
    modelo.error = _error_proveedor(codigo)
    _, fila, _ = ejecutar(sesion, modelo=modelo)
    assert fila.decision is None and fila.prioridad == 0
    assert "LLM_REFUSAL" in fila.marcas_pipeline
    assert "RD-16" in fila.reglas_aplicadas


def test_08_reintento_exitoso(sesion):
    estado, fila, modelo = ejecutar(sesion, modelo=ModeloFalso(invalidas=1))
    assert modelo.tipificaciones == 2
    assert estado["intentos_validacion"] == 1
    assert fila.justificacion_y_citas[0]["citas"][0]["texto_literal"] == estado[
        "texto_seudonimizado"]
    assert fila.prioridad == 3


def test_09_un_solo_reintento(sesion):
    _, fila, modelo = ejecutar(sesion, modelo=ModeloFalso(invalidas=99))
    assert modelo.tipificaciones == 2
    assert "RD-15" in fila.reglas_aplicadas and fila.prioridad == 1


def test_10_auditoria(sesion):
    estado, fila, _ = ejecutar(sesion)
    assert verificar_cadena(sesion, fila.denuncia_id)
    eventos = list(sesion.scalars(select(EventoAuditoria)))
    assert [e.accion for e in eventos] == ["ingesta", "preclasificacion"]
    texto_eventos = json.dumps([e.detalle for e in eventos])
    assert "Trabajo en" not in texto_eventos
    for original in estado["mapa_seudonimos"].values():
        assert original not in texto_eventos
    assert not any("mapa" in columna.name for columna in Preclasificacion.__table__.columns)


@pytest.mark.parametrize("opcion", ["refusal_en", "presupuesto_en"])
def test_corte_en_tipificacion(sesion, opcion):
    _, fila, modelo = ejecutar(sesion, modelo=ModeloFalso(**{opcion: 2}))
    assert len(modelo.llamadas) == 2
    assert fila.decision is None and fila.prioridad == 0


def test_procesar_caso_persistencia_transaccional(sesion):
    identificador = procesar_caso(CASOS["G-04"]["entrada"], Contexto(sesion, ModeloFalso()))
    sesion.commit()
    assert sesion.scalar(select(Preclasificacion.denuncia_id)) == identificador


def test_11_decision_corregida_queda_registrada(sesion):
    """Si una regla cambia la decision, hay que poder saber que propuso el modelo.

    Sin esto, el funcionario ve una decision PROCEDE_INVESTIGACION junto a una
    justificacion que argumenta a favor de la mediacion, y nada indica que una
    regla intervino. La contradiccion se ve, pero su origen no, y el sistema
    deja de ser auditable justo en el caso que mas importa.
    """
    _, fila, _ = ejecutar(sesion, "G-02", ModeloFalso(sexual=True))
    bloque = fila.justificacion_y_citas[0]
    assert bloque["decision_modelo"] == "DERIVA_MEDIACION"
    assert fila.decision == "PROCEDE_INVESTIGACION"
    assert "RD-10" in fila.reglas_aplicadas


def test_12_sin_correccion_la_decision_del_modelo_coincide(sesion):
    _, fila, _ = ejecutar(sesion)
    bloque = fila.justificacion_y_citas[0]
    assert bloque["decision_modelo"] == fila.decision == "PROCEDE_INVESTIGACION"


def test_empleador_municipal_se_guarda_como_empresa(sesion):
    _, fila, _ = ejecutar(sesion, "G-04")
    assert sesion.get(Denuncia, fila.denuncia_id).empleador == "[EMPRESA_1]"


def test_extraccion_recibe_sector_y_tipo_de_ingreso(sesion):
    estado, _, modelo = ejecutar(sesion, "G-01")
    extraccion = modelo.llamadas[0]["contenido_usuario"]
    assert "<campos_ingreso>\ntipo_ingreso: DIRECTA\nsector_empleador: PRIVADO\n" in extraccion
    # El bloque va fuera de <denuncia>: el relato que se cita no cambia.
    denuncia = extraccion.split("<denuncia>\n")[1].split("\n</denuncia>")[0]
    assert denuncia == estado["texto_seudonimizado"]
