"""Cliente sin herramientas ni registro de contenido; transacción del llamador."""

import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import anthropic
from pydantic import BaseModel
from sqlalchemy import select

from karin_triage.config import AjustesNucleo
from karin_triage.models.tablas import UsoDiario

# Tarifas de claude-sonnet-5, noviembre de 2026. PENDIENTE_VERIFICAR contra el
# tarifario vigente antes de cualquier uso real.
USD_ENTRADA_MILLON = 2.0
USD_SALIDA_MILLON = 10.0
# Los tokens leidos de cache se facturan aparte y mucho mas barato que la
# entrada nueva: `usage.input_tokens` NO los incluye. Ignorarlos subestima el
# costo, y como este numero alimenta el tope de gasto en dolares, el tope deja
# de morder cuando deberia. Se usa el 10% de la entrada, que es la proporcion
# habitual. PENDIENTE_VERIFICAR el factor exacto.
FACTOR_CACHE_LECTURA = 0.1
USD_CACHE_LECTURA_MILLON = USD_ENTRADA_MILLON * FACTOR_CACHE_LECTURA
NOMBRE_PREFIJO = "prefijo_normativo.md"
client = None
logger = logging.getLogger(__name__)


def resolver_prefijo() -> Path:
    """Localiza `prompts/prefijo_normativo.md` sin depender del modo de instalación.

    Una ruta calculada con un número fijo de `parents` desde `__file__` funciona
    con una instalación editable, que es la que deja `uv sync`, y **falla con una
    instalación normal**, que es la que hace el `Dockerfile`: ahí el paquete vive
    en `site-packages` y la ruta cae dentro del entorno virtual. El síntoma sería
    que toda llamada al modelo falla dentro del contenedor y funciona en local.

    Orden de búsqueda: la variable `KARIN_PROMPTS_DIR`, y si no está, se sube por
    los directorios padres buscando `prompts/<nombre>`.
    """
    directorio = os.getenv("KARIN_PROMPTS_DIR")
    if directorio:
        ruta = Path(directorio) / NOMBRE_PREFIJO
        if not ruta.is_file():
            raise FileNotFoundError(f"KARIN_PROMPTS_DIR no contiene {NOMBRE_PREFIJO}: {ruta}")
        return ruta
    for padre in Path(__file__).resolve().parents:
        ruta = padre / "prompts" / NOMBRE_PREFIJO
        if ruta.is_file():
            return ruta
    raise FileNotFoundError(
        f"No se encontro prompts/{NOMBRE_PREFIJO} subiendo desde {__file__}. "
        "Define KARIN_PROMPTS_DIR."
    )


@lru_cache(maxsize=1)
def leer_prefijo():
    # read_bytes evita la traducción de CRLF: conserva el contenido byte a byte.
    # Se lee una sola vez por proceso: releerlo rompería el cache del prefijo.
    return resolver_prefijo().read_bytes().decode("utf-8")


@dataclass(frozen=True)
class RespuestaLLM:
    datos: BaseModel | None
    refusal: bool
    stop_reason: str | None
    tokens_entrada: int
    tokens_salida: int
    cache_read_tokens: int
    costo_usd: float


class PresupuestoAgotado(Exception):
    pass


def llamar(prompt_nodo, contenido_usuario, formato, effort, sesion) -> RespuestaLLM:
    if effort not in {"low", "medium"}:
        raise ValueError("effort debe ser low o medium")
    ajustes = AjustesNucleo()
    hoy = datetime.now(UTC).date()
    uso = sesion.scalar(select(UsoDiario).where(UsoDiario.fecha == hoy).with_for_update())
    if uso is None:
        uso = UsoDiario(fecha=hoy, llamadas=0, usd=0.0)
        sesion.add(uso)
        sesion.flush()
    if uso.llamadas >= ajustes.tope_llamadas_dia or uso.usd >= ajustes.tope_usd_dia:
        raise PresupuestoAgotado("PRESUPUESTO_AGOTADO")
    # Desactiva los reintentos internos para limitar el total a dos intentos.
    cliente = client if client is not None else anthropic.Anthropic(max_retries=0)
    for intento in range(2):
        try:
            response = cliente.messages.parse(
                model=ajustes.modelo,
                max_tokens=16000,
                system=[
                    {
                        "type": "text",
                        "text": leer_prefijo(),
                        "cache_control": {"type": "ephemeral", "ttl": "1h"},
                    },
                    {
                        "type": "text",
                        "text": prompt_nodo,
                        "cache_control": {"type": "ephemeral", "ttl": "1h"},
                    },
                ],
                messages=[{"role": "user", "content": contenido_usuario}],
                output_format=formato,
                output_config={"effort": effort},
            )
            break
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as exc:
            reintentable = isinstance(exc, anthropic.APIConnectionError) or exc.status_code >= 500
            if not reintentable or intento == 1:
                raise
            time.sleep(2**intento)
    refusal = response.stop_reason == "refusal"
    datos = None if refusal else response.parsed_output
    entrada, salida = response.usage.input_tokens, response.usage.output_tokens
    cache = response.usage.cache_read_input_tokens or 0
    costo = (entrada * USD_ENTRADA_MILLON + salida * USD_SALIDA_MILLON
             + cache * USD_CACHE_LECTURA_MILLON) / 1_000_000
    uso.llamadas += 1
    uso.usd += costo
    sesion.flush()
    logger.info(
        "nodo=%s tokens_entrada=%s tokens_salida=%s cache_read_tokens=%s costo=%s stop_reason=%s",
        formato.__name__,
        entrada,
        salida,
        cache,
        costo,
        response.stop_reason,
    )
    return RespuestaLLM(datos, refusal, response.stop_reason, entrada, salida, cache, costo)
