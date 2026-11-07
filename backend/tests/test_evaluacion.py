"""Regresiones de métricas y validación por fuente sin llamadas externas."""
import importlib.util
from pathlib import Path

from karin_triage.core.reglas import rd_15
from karin_triage.models.salidas_llm import Cita, PropuestaClasificacion

spec = importlib.util.spec_from_file_location("runner", Path(__file__).parents[2] / "evals/runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_normativa_se_contrasta_con_prefijo():
    cita = {"texto_literal": "frase de la norma", "fuente": "normativa"}
    assert runner.literal(cita, "otro relato", "Aquí está frase de la norma.")
    assert not runner.literal(cita, "frase de la norma", "norma diferente")
    assert not runner.literal({"texto_literal": "", "fuente": "denuncia"}, "texto", "norma")


def test_rd15_distingue_fuentes():
    propuesta = PropuestaClasificacion(
        informacion_suficiente=True, decision="PROCEDE_INVESTIGACION", tipo_conducta=[],
        vulneracion_ddff=False, motivo_descarte=None, urgencia_resguardo=False,
        confianza=0.8, justificacion="Caso sintético", supuestos=[],
        citas=[Cita(texto_literal="norma exacta", fuente="normativa")])
    assert not rd_15(propuesta, "relato", prefijo_normativo="norma exacta").aplico
    assert rd_15(propuesta, "norma exacta", prefijo_normativo="otra").aplico


def test_metricas_no_inflan_errores_y_detectan_sexual_sin_id_especial():
    detalle = [
        {"id": "sin-modelo", "hubo_llm": False, "estado_auxiliar_esperado": "X", "estado_auxiliar_correcto": True},
        {"id": "error", "hubo_llm": True, "error": "ValidationError", "decision_esperada": "PROCEDE_INVESTIGACION", "urgencia_esperada": True},
        {"id": "independiente", "hubo_llm": True, "propuesta_valida": True,
         "reintento_de_validacion": False, "tipos_esperados": ["ACOSO_SEXUAL"],
         "decision_del_modelo": "DERIVA_MEDIACION", "urgencia_esperada": False, "urgencia_obtenida": True},
    ]
    m = runner.metricas(detalle)
    assert m["salida_validada_sin_reintento"] == "1/2"
    assert m["acoso_sexual_a_mediacion_por_el_modelo"] == 1
    assert m["urgencia_correcta"] == "0/2" and m["errores"] == 1
    assert m["json_valido_al_primer_intento"] is None
