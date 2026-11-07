"""Estado efímero: el relato y el mapa nunca se serializan en disco."""

from typing import TypedDict


class EstadoTriage(TypedDict, total=False):
    entrada: dict
    denuncia_id: str
    texto_seudonimizado: str
    mapa_seudonimos: dict
    hallazgos_pii: list[str]
    estado_auxiliar: str | None
    marcas: list[str]
    reglas: list[dict]
    hechos: dict | None
    propuesta: dict | None
    # Lo que propuso el modelo ANTES de que las reglas posteriores lo
    # corrigieran. Se persiste para que el funcionario pueda ver que una
    # regla intervino, en vez de encontrarse una decision que contradice su
    # propia justificacion sin explicacion visible.
    decision_modelo: str | None
    intentos_validacion: int
    prioridad: int
    inyeccion_detectada: bool
    llamadas_llm: int
    costo_usd: float
    tokens_entrada: int
    tokens_salida: int
    cache_read_tokens: int
