"""Pruebas exclusivamente sintéticas del núcleo determinista."""

from dataclasses import replace
from datetime import date

import pytest
from pydantic import ValidationError

from karin_triage.core import reglas as r
from karin_triage.core.taxonomia import EstadoAuxiliar, MarcaPipeline, SectorEmpleador, TipoIngreso
from karin_triage.models.salidas_llm import Cita, HechosExtraidos, PropuestaClasificacion


@pytest.fixture
def entrada():
    return r.EntradaDenuncia("Relato sintético", "Entidad sintética", date(2025, 1, 1),
                             TipoIngreso.DIRECTA, SectorEmpleador.PRIVADO, "hash-sintetico")


@pytest.fixture
def propuesta():
    return PropuestaClasificacion(
        informacion_suficiente=True, decision="DERIVA_MEDIACION", tipo_conducta=[],
        vulneracion_ddff=False, motivo_descarte=None, urgencia_resguardo=False,
        confianza=0.9, justificacion="Conducta sintética descrita.",
        citas=[Cita(texto_literal="Relato sintético", fuente="denuncia")], supuestos=[],
    )


@pytest.fixture
def hechos():
    return HechosExtraidos(
        relacion_laboral_declarada=True, empleador_sector="PRIVADO", conductas_descritas=[],
        reiteracion="UNICA", rol_persona_denunciada="PAR", indicios_riesgo_inmediato=[],
        efectos_declarados=[], citas=[],
    )


@pytest.mark.parametrize("cambio", [
    {"relato": None}, {"relato": "  "}, {"empleador": None}, {"empleador": " "},
    {"fecha_denuncia": None},
])
def test_rd_01(entrada, cambio):
    resultado = r.rd_01(replace(entrada, **cambio))
    assert (resultado.id, resultado.aplico, resultado.efecto) == (
        "RD-01", True, "REQUIERE_ANTECEDENTES")


def test_rd_02(entrada):
    assert r.rd_02(replace(entrada, sector_empleador=SectorEmpleador.PUBLICO)).aplico


def test_rd_03(entrada):
    resultado = r.rd_03(replace(entrada, tipo_ingreso=TipoIngreso.INFORME_INTERNO))
    assert resultado.aplico and "30 días" in resultado.detalle


def test_rd_04(entrada):
    resultado = r.rd_04(replace(entrada, hashes_previos=[entrada.hash_contenido]))
    assert resultado.aplico and resultado.efecto == "REVISION_DUPLICADA"
    assert entrada.hashes_previos == []


@pytest.mark.parametrize("fecha,aplica", [(date(2024, 7, 31), True),
                                          (date(2024, 8, 1), False), (None, False)])
def test_rd_05(entrada, fecha, aplica):
    assert r.rd_05(replace(entrada, fecha_denuncia=fecha)).aplico is aplica


def test_rd_06():
    assert r.rd_06(["hallazgo sintético"]).efecto == "PII_RESIDUAL"
    assert not r.rd_06([]).aplico


def test_rd_10_y_copia(propuesta, hechos):
    propuesta.tipo_conducta = ["ACOSO_SEXUAL"]
    original = propuesta.model_dump()
    copia, resultados = r.aplicar_reglas_post(propuesta, "Relato sintético", hechos)
    assert copia.decision == "PROCEDE_INVESTIGACION"
    assert resultados[0].id == "RD-10" and resultados[0].aplico
    assert copia.urgencia_resguardo
    assert propuesta.model_dump() == original
    assert [x.id for x in resultados] == ["RD-10", "RD-11", "RD-15", "RD-12", "RD-13", "RD-14"]
    copia.citas.clear()
    assert propuesta.citas


@pytest.mark.parametrize("expresion", r.EXPRESIONES_FALTA_PRUEBA)
def test_rd_11_falta_prueba(propuesta, expresion):
    copia = propuesta.model_copy(update={"decision": "DESCARTADO",
        "motivo_descarte": "NO_CONFIGURA_CONDUCTA", "justificacion": expresion.upper()})
    assert r.rd_11(copia).aplico


def test_rd_11_catalogo_y_citas(propuesta):
    copia = propuesta.model_copy(update={"decision": "DESCARTADO"})
    assert r.rd_11(copia).aplico
    copia.motivo_descarte = "DESISTIMIENTO"
    assert not r.rd_11(copia).aplico
    copia.citas = []
    assert r.rd_11(copia).aplico
    assert not r.rd_11(propuesta).aplico


@pytest.mark.parametrize("termino", r.TERMINOS_RIESGO)
def test_rd_12_indicios(propuesta, hechos, termino):
    assert r.rd_12(propuesta, termino.upper(), hechos).aplico


def test_rd_12_asimetrica(propuesta, hechos):
    copia = propuesta.model_copy(update={"urgencia_resguardo": True})
    resultado = r.rd_12(copia, "sin indicios", hechos)
    assert not resultado.aplico and "ya activa" in resultado.detalle
    salida, _ = r.aplicar_reglas_post(copia, "Relato sintético", hechos)
    assert salida.urgencia_resguardo
    assert r.rd_12(propuesta, "empujó", hechos).aplico
    hechos.indicios_riesgo_inmediato = ["amenaza"]
    assert r.rd_12(propuesta, "", hechos).aplico


def test_rd12_distingue_amenaza_laboral_de_fisica(propuesta, hechos):
    hechos.indicios_riesgo_inmediato = ["Amenaza de dejar sin turnos"]
    assert not r.rd_12(propuesta, "Me dijo que me dejaría sin turnos", hechos).aplico
    assert r.rd_12(propuesta, "Amenaza de despido y de golpearme hoy", hechos).aplico
    copia = propuesta.model_copy(update={"urgencia_resguardo": True})
    salida, _ = r.aplicar_reglas_post(copia, "Amenaza de despido", hechos)
    assert salida.urgencia_resguardo


@pytest.mark.parametrize("confianza,aplica", [(0.74, True), (0.75, False), (1, False)])
def test_rd_13(propuesta, confianza, aplica):
    assert r.rd_13(propuesta.model_copy(update={"confianza": confianza})).aplico is aplica


def test_rd_14(propuesta):
    resultado = r.rd_14(propuesta.model_copy(update={"decision": "DESCARTADO"}))
    assert resultado.aplico and "supervisor" in resultado.detalle
    assert not r.rd_14(propuesta).aplico


@pytest.mark.parametrize("texto,aplica", [
    ("Relato  \n sintético", False), ("Relato parecido", True),
    ("relato sintético", True), ("Relato sintetico", True),
])
def test_rd_15(propuesta, texto, aplica):
    resultado = r.rd_15(propuesta, texto)
    assert resultado.aplico is aplica
    if aplica:
        assert resultado.efecto == "REINTENTO"
        assert r.rd_15(propuesta, texto, reintentos=1).efecto == "REVISION_PRIORITARIA"


@pytest.mark.parametrize("fuente", ["denuncia", "normativa"])
def test_rd_15_cita_vacia(propuesta, fuente):
    propuesta.citas = [Cita(texto_literal=" ", fuente=fuente)]
    assert r.rd_15(propuesta, "texto").aplico


@pytest.mark.parametrize("stop,error,aplica", [("refusal", False, True),
    (None, True, True), ("end_turn", False, False)])
def test_rd_16(stop, error, aplica):
    resultado = r.rd_16(stop, error)
    assert resultado.id == "RD-16" and resultado.aplico is aplica


@pytest.mark.parametrize("cambio,pii,esperado,ids", [
    ({"sector_empleador": SectorEmpleador.PUBLICO, "relato": None}, [],
     EstadoAuxiliar.DERIVAR_OTRA_INSTITUCION, [4, 2]),
    ({"relato": None}, ["hallazgo sintético"], MarcaPipeline.PII_RESIDUAL, [4, 2, 3, 6]),
    ({"tipo_ingreso": TipoIngreso.INFORME_INTERNO}, ["hallazgo sintético"],
     MarcaPipeline.FUERA_DE_ALCANCE, [4, 2, 3]),
    ({"relato": None}, [], EstadoAuxiliar.REQUIERE_ANTECEDENTES, [4, 2, 3, 6, 1]),
    ({"fecha_denuncia": date(2024, 1, 1)}, [], MarcaPipeline.REGIMEN_ANTERIOR,
     [4, 2, 3, 6, 1, 5]),
    ({}, [], None, [4, 2, 3, 6, 1, 5]),
])
def test_precedencia(entrada, cambio, pii, esperado, ids):
    entrada = replace(entrada, hashes_previos=[entrada.hash_contenido], **cambio)
    efecto, resultados = r.aplicar_reglas_previas(entrada, pii)
    assert efecto == esperado
    assert [x.id for x in resultados] == [f"RD-{i:02}" for i in ids]
    assert resultados[0].aplico


@pytest.mark.parametrize("confianza", [-0.01, 1.01])
def test_validacion_pydantic(propuesta, confianza):
    with pytest.raises(ValidationError):
        PropuestaClasificacion.model_validate({**propuesta.model_dump(), "confianza": confianza})


def test_ids_y_no_aplicacion(entrada, propuesta, hechos):
    resultados = [r.rd_01(entrada), r.rd_02(entrada), r.rd_03(entrada), r.rd_04(entrada),
                  r.rd_05(entrada), r.rd_06([]),
                  r.rd_10(propuesta), r.rd_11(propuesta), r.rd_12(propuesta, "", hechos),
                  r.rd_13(propuesta), r.rd_14(propuesta),
                  r.rd_15(propuesta, "Relato sintético"), r.rd_16()]
    # El catalogo salta de RD-06 a RD-10: RD-07 a RD-09 quedaron reservados.
    catalogo = [f"RD-{i:02}" for i in [*range(1, 7), *range(10, 17)]]
    assert [x.id for x in resultados] == catalogo
    assert all(not x.aplico and x.efecto is None for x in resultados)


def test_rd_15_rechaza_una_propuesta_sin_ninguna_cita(propuesta):
    # Sin esta condicion, any() sobre una lista vacia da False y una propuesta
    # sin fundamento pasaria la verificacion por vacuidad. RD-11 solo cubre el
    # caso DESCARTADO, asi que un PROCEDE_INVESTIGACION sin citas se habria
    # persistido sin que ninguna regla lo marcara.
    propuesta.citas = []
    propuesta.decision = "PROCEDE_INVESTIGACION"
    resultado = r.rd_15(propuesta, "Relato sintetico cualquiera")
    assert resultado.aplico
    assert resultado.id == "RD-15"
    assert "sin ninguna cita" in resultado.detalle
