"""La referencia sintética se carga desde la raíz, sin omisiones silenciosas."""

import json
from pathlib import Path

import pytest

from karin_triage.services.seudonimizador import detectar_pii_residual, seudonimizar


def _casos():
    ruta = Path(__file__).resolve().parents[2] / "golden_set" / "denuncias.jsonl"
    if not ruta.is_file():
        pytest.fail("Falta golden_set/denuncias.jsonl: no es posible comprobar la fuga de PII")
    casos = [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]
    assert len(casos) == 8, "El golden set debe contener los ocho casos sintéticos"
    return casos


@pytest.mark.parametrize("caso", _casos(), ids=lambda caso: caso["id"])
def test_sin_fuga_golden_set(caso):
    entrada = caso["entrada"]
    empleador = entrada["empleador"]
    resultado = seudonimizar(entrada["relato"], nombres_conocidos=[empleador])
    for valor in caso["esperado"]["seudonimizacion_esperada"]:
        assert valor.casefold() not in resultado.texto.casefold(), "PII esperada sin sustituir"
    assert detectar_pii_residual(resultado.texto) == []
    if empleador:
        assert empleador.casefold() not in resultado.texto.casefold(), "Empleador sin sustituir"
