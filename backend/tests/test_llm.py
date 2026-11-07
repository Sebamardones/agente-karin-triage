"""Dobles sin red ni clave del modelo."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import anthropic
import httpx
import pytest
import test_persistencia
from pydantic import BaseModel

from karin_triage.models.tablas import UsoDiario
from karin_triage.services import llm


@pytest.fixture
def sesion():
    yield from test_persistencia.sesion.__wrapped__()


@pytest.fixture
def ajustes_env(monkeypatch):
    test_persistencia.ajustes_env.__wrapped__(monkeypatch)


class Salida(BaseModel):
    valor: str


@pytest.fixture
def cliente(ajustes_env, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    doble = Mock()
    doble.messages.parse.return_value = SimpleNamespace(
        stop_reason="end_turn",
        parsed_output=Salida(valor="sintetico"),
        usage=SimpleNamespace(input_tokens=10000, output_tokens=2000, cache_read_input_tokens=3000),
    )
    monkeypatch.setattr(llm, "client", doble)
    monkeypatch.setattr(llm.time, "sleep", Mock())
    llm.leer_prefijo.cache_clear()
    yield doble
    llm.leer_prefijo.cache_clear()


def invocar(sesion):
    return llm.llamar(
        "nodo sintetico", "<denuncia>dato sintetico</denuncia>", Salida, "low", sesion
    )


def test_feliz_y_contrato(cliente, sesion):
    respuesta = invocar(sesion)
    assert respuesta.datos == Salida(valor="sintetico")
    assert not respuesta.refusal
    # Entrada  10.000 x USD  2/M = 0,0200
    # Salida    2.000 x USD 10/M = 0,0200
    # Cache     3.000 x USD 0,20/M = 0,0006   <- antes se ignoraba
    #                              -----------
    #                                0,0406
    # `usage.input_tokens` no incluye los tokens servidos desde cache, asi que
    # ignorarlos subestima el costo, y ese numero es el que alimenta el tope de
    # gasto en dolares.
    COSTO_POR_LLAMADA = 0.0406
    assert respuesta.costo_usd == pytest.approx(COSTO_POR_LLAMADA)
    assert (respuesta.tokens_entrada, respuesta.tokens_salida, respuesta.cache_read_tokens) == (
        10000,
        2000,
        3000,
    )
    invocar(sesion)
    uso = sesion.get(UsoDiario, datetime.now(UTC).date())
    assert uso.llamadas == 2
    assert uso.usd == pytest.approx(2 * COSTO_POR_LLAMADA)
    kwargs = cliente.messages.parse.call_args.kwargs
    assert kwargs["max_tokens"] == 16000
    assert kwargs["output_format"] is Salida
    assert kwargs["output_config"] == {"effort": "low"}
    assert len(kwargs["system"]) == 2
    assert all(b["cache_control"] == {"type": "ephemeral", "ttl": "1h"} for b in kwargs["system"])
    assert not {"tools", "thinking", "tool_choice", "fallbacks", "extra_headers"} & kwargs.keys()


def test_refusal_sin_leer_contenido(cliente, sesion):
    # Sin parsed_output: acceder antes de comprobar refusal har?a fallar el test.
    original = cliente.messages.parse.return_value
    cliente.messages.parse.return_value = SimpleNamespace(
        stop_reason="refusal", usage=original.usage
    )
    respuesta = invocar(sesion)
    assert respuesta.refusal and respuesta.datos is None
    assert cliente.messages.parse.call_count == 1


@pytest.mark.parametrize("llamadas,usd", [(200, 0), (0, 3)])
def test_topes(cliente, sesion, llamadas, usd):
    sesion.add(UsoDiario(fecha=datetime.now(UTC).date(), llamadas=llamadas, usd=usd))
    sesion.flush()
    with pytest.raises(llm.PresupuestoAgotado):
        invocar(sesion)
    cliente.messages.parse.assert_not_called()


@pytest.mark.parametrize("codigo", [None, 500, 400])
def test_reintentos(cliente, sesion, codigo):
    request = httpx.Request("POST", "https://example.invalid")
    error = (
        anthropic.APIConnectionError(request=request)
        if codigo is None
        else anthropic.APIStatusError(
            "sintetico", response=httpx.Response(codigo, request=request), body=None
        )
    )
    respuesta = cliente.messages.parse.return_value
    cliente.messages.parse.side_effect = [error, respuesta]
    if codigo == 400:
        with pytest.raises(anthropic.APIStatusError):
            invocar(sesion)
        assert cliente.messages.parse.call_count == 1
    else:
        assert invocar(sesion).datos == respuesta.parsed_output
        assert cliente.messages.parse.call_count == 2
        llm.time.sleep.assert_called_once_with(1)


def test_prefijo_una_lectura(cliente, sesion, monkeypatch, tmp_path):
    archivo = tmp_path / llm.NOMBRE_PREFIJO
    archivo.write_bytes(b"prefijo\r\nsintetico\r\n")
    monkeypatch.setenv("KARIN_PROMPTS_DIR", str(tmp_path))
    llm.leer_prefijo.cache_clear()
    for _ in range(3):
        invocar(sesion)
        archivo.write_bytes(b"cambiado")
    assert llm.leer_prefijo.cache_info().misses == 1
    assert all(
        c.kwargs["system"][0]["text"] == "prefijo\r\nsintetico\r\n"
        for c in cliente.messages.parse.call_args_list
    )


# --- Regresion: resolucion de la ruta del prefijo ---------------------------
# La version anterior calculaba la ruta con un numero fijo de `parents` desde
# `__file__`. Eso funciona con la instalacion editable que deja `uv sync` y
# falla con una instalacion normal, que es la del Dockerfile: el paquete queda
# en site-packages y la ruta cae dentro del entorno virtual. El sintoma habria
# sido que toda llamada al modelo funciona en local y falla en el contenedor.


def test_resuelve_el_prefijo_real_del_repositorio(monkeypatch):
    monkeypatch.delenv("KARIN_PROMPTS_DIR", raising=False)
    ruta = llm.resolver_prefijo()
    assert ruta.is_file()
    assert ruta.name == llm.NOMBRE_PREFIJO
    assert ruta.parent.name == "prompts"


def test_la_variable_de_entorno_gana_sobre_la_busqueda(monkeypatch, tmp_path):
    (tmp_path / llm.NOMBRE_PREFIJO).write_text("otro", encoding="utf-8")
    monkeypatch.setenv("KARIN_PROMPTS_DIR", str(tmp_path))
    assert llm.resolver_prefijo().parent == tmp_path


def test_falla_con_mensaje_claro_si_la_variable_apunta_mal(monkeypatch, tmp_path):
    monkeypatch.setenv("KARIN_PROMPTS_DIR", str(tmp_path / "vacio"))
    with pytest.raises(FileNotFoundError, match=llm.NOMBRE_PREFIJO):
        llm.resolver_prefijo()


def test_el_costo_incluye_los_tokens_leidos_de_cache(cliente, sesion, monkeypatch):
    """Regresion: la formula ignoraba `cache_read_input_tokens` por completo.

    `usage.input_tokens` no incluye los tokens servidos desde cache, asi que
    ignorarlos subestima el costo real. Como ese numero es el que acumula
    `uso_diario`, el tope de gasto en dolares dejaba de morder cuando debia.
    """
    base = llm.llamar("nodo", "<denuncia>x</denuncia>", Salida, "low", sesion).costo_usd
    monkeypatch.setattr(llm, "FACTOR_CACHE_LECTURA", 0.0)
    monkeypatch.setattr(llm, "USD_CACHE_LECTURA_MILLON", 0.0)
    sin_cache = llm.llamar("nodo", "<denuncia>x</denuncia>", Salida, "low", sesion).costo_usd
    assert base > sin_cache, "el costo con cache tiene que ser mayor que ignorandolo"
    assert base - sin_cache == pytest.approx(3000 * 0.2 / 1_000_000)
