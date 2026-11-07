"""Reglas duras deterministas RD-01 a RD-16.

Ninguna usa el LLM y ninguna decide: todos los efectos son propuestas que
terminan en revisión humana, y cada evaluación queda registrada para que
`reglas_aplicadas[]` sea auditable.

La numeración salta de RD-06 a RD-10 porque ese es el catálogo de la
arquitectura: RD-07 a RD-09 quedaron reservados y nunca se especificaron. No se
implementan: una regla vacía con un identificador reservado es peor que la
ausencia declarada.

Precedencia: RD-02/RD-03 > RD-06 > RD-01 > RD-05 > LLM > RD-10 > RD-11/RD-15
> RD-12 > RD-13/RD-14.
"""

import unicodedata
from dataclasses import dataclass, field
from datetime import date

from karin_triage.core.taxonomia import (
    FECHA_VIGENCIA_LEY,
    UMBRAL_CONFIANZA,
    EstadoAuxiliar,
    MarcaPipeline,
    MotivoDescarte,
    SectorEmpleador,
    TipoIngreso,
)
from karin_triage.models.salidas_llm import HechosExtraidos, PropuestaClasificacion

EXPRESIONES_FALTA_PRUEBA = (
    "falta de prueba", "sin pruebas", "no hay pruebas", "insuficiencia probatoria",
    "no acredita", "falta de evidencia",
)
TERMINOS_RIESGO = (
    "golpe", "empujo", "amenaza", "arma", "agresion fisica", "acoso sexual",
    "tocaciones", "convive", "vive con",
)


@dataclass
class ResultadoRegla:
    id: str
    aplico: bool
    efecto: str | None
    detalle: str


@dataclass
class EntradaDenuncia:
    relato: str | None
    empleador: str | None
    fecha_denuncia: date | None
    tipo_ingreso: TipoIngreso
    sector_empleador: SectorEmpleador
    hash_contenido: str
    hashes_previos: list[str] = field(default_factory=list)


def _resultado(numero: int, aplica: bool, efecto: str, detalle: str) -> ResultadoRegla:
    return ResultadoRegla(f"RD-{numero:02}", aplica, efecto if aplica else None, detalle)


def _normalizar(texto: str) -> str:
    return "".join(
        letra for letra in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(letra) != "Mn"
    )


def rd_01(entrada: EntradaDenuncia) -> ResultadoRegla:
    falta = not (entrada.relato or "").strip() or not (entrada.empleador or "").strip()
    return _resultado(1, falta or entrada.fecha_denuncia is None,
                      "REQUIERE_ANTECEDENTES", "Validación de campos obligatorios.")


def rd_02(entrada: EntradaDenuncia) -> ResultadoRegla:
    return _resultado(2, entrada.sector_empleador == SectorEmpleador.PUBLICO,
                      "DERIVAR_OTRA_INSTITUCION", "Sector público: revisión humana de derivación.")


def rd_03(entrada: EntradaDenuncia) -> ResultadoRegla:
    return _resultado(3, entrada.tipo_ingreso == TipoIngreso.INFORME_INTERNO,
                      "FUERA_DE_ALCANCE", "Alerta de plazo de 30 días; revisión humana.")


def rd_04(entrada: EntradaDenuncia) -> ResultadoRegla:
    return _resultado(4, entrada.hash_contenido in entrada.hashes_previos,
                      "REVISION_DUPLICADA", "Candidata a DUPLICADA; nunca descarte automático.")


def rd_05(entrada: EntradaDenuncia) -> ResultadoRegla:
    return _resultado(5, entrada.fecha_denuncia is not None
                      and entrada.fecha_denuncia < FECHA_VIGENCIA_LEY,
                      "REGIMEN_ANTERIOR", "Régimen anterior: revisión humana.")


def rd_06(hallazgos_pii: list[str]) -> ResultadoRegla:
    return _resultado(6, bool(hallazgos_pii), "PII_RESIDUAL",
                      "Bloquear flujo sin llamar al LLM; no registrar los hallazgos sensibles.")


def rd_10(propuesta: PropuestaClasificacion) -> ResultadoRegla:
    # Verificada contra el texto literal: el art. 211-D inc. final remite al
    # art. 486 "con excepción de lo consagrado en el inciso sexto respecto a las
    # conductas establecidas en la letra a) del artículo 2", y la letra a) es el
    # acoso sexual. La mediación previa del inciso sexto no le aplica.
    return _resultado(10, "ACOSO_SEXUAL" in propuesta.tipo_conducta
                      and propuesta.decision == "DERIVA_MEDIACION",
                      "PROCEDE_INVESTIGACION", "Corregir propuesta; requiere revisión humana.")


def rd_11(propuesta: PropuestaClasificacion) -> ResultadoRegla:
    sin_prueba = any(t in _normalizar(propuesta.justificacion) for t in EXPRESIONES_FALTA_PRUEBA)
    invalida = (propuesta.motivo_descarte not in {m.value for m in MotivoDescarte}
                or not propuesta.citas or sin_prueba)
    return _resultado(11, propuesta.decision == "DESCARTADO" and invalida,
                      "PROPUESTA_INVALIDA", "Descarte inválido: revisión prioritaria.")


def rd_12(propuesta: PropuestaClasificacion, texto_seudonimizado: str,
          hechos: HechosExtraidos) -> ResultadoRegla:
    if propuesta.urgencia_resguardo:
        return ResultadoRegla("RD-12", False, None, "Urgencia ya activa; se conserva.")
    texto = _normalizar(" ".join([
        texto_seudonimizado, *hechos.conductas_descritas,
        *hechos.indicios_riesgo_inmediato, *hechos.efectos_declarados,
    ]))
    riesgo = (
        "ACOSO_SEXUAL" in propuesta.tipo_conducta or any(t in texto for t in TERMINOS_RIESGO)
    )
    return _resultado(12, riesgo, "URGENCIA_RESGUARDO", "Elevar urgencia para revisión humana.")


def rd_13(propuesta: PropuestaClasificacion) -> ResultadoRegla:
    return _resultado(13, propuesta.confianza < UMBRAL_CONFIANZA,
                      "REVISION_PRIORITARIA", "Evaluación del umbral de confianza.")


def rd_14(propuesta: PropuestaClasificacion) -> ResultadoRegla:
    return _resultado(14, propuesta.decision == "DESCARTADO", "DOBLE_REVISION",
                      "Segunda revisión por funcionario distinto con rol supervisor.")


def rd_15(propuesta: PropuestaClasificacion, texto_seudonimizado: str,
          reintentos: int = 0) -> ResultadoRegla:
    """Verificación literal de las citas, y exigencia de que exista al menos una.

    La comparación normaliza **solo** los espacios en blanco consecutivos: un
    acento cambiado o una letra corregida no es una cita literal.

    Una propuesta con `citas` vacía también es inválida. No es un añadido
    cosmético: sin esa condición, `any()` sobre una lista vacía da `False` y una
    propuesta sin ningún fundamento pasaría la verificación por vacuidad. RD-11
    cubre ese caso solo cuando la decisión es `DESCARTADO`, así que un
    `PROCEDE_INVESTIGACION` sin una sola cita se habría persistido sin que
    ninguna regla lo marcara, y el funcionario habría recibido una decisión que
    no puede auditar.
    """
    texto = " ".join(texto_seudonimizado.split())
    sin_citas = not propuesta.citas
    no_literal = any(not (cita := " ".join(c.texto_literal.split())) or cita not in texto
                     for c in propuesta.citas)
    efecto = "REINTENTO" if reintentos == 0 else "REVISION_PRIORITARIA"
    detalle = ("Propuesta sin ninguna cita: no es auditable." if sin_citas else
               "Propuesta inválida si cita no literal; máximo un reintento, luego prioridad.")
    return _resultado(15, sin_citas or no_literal, efecto, detalle)


def rd_16(stop_reason: str | None = None,
          error_tras_reintentos: bool = False) -> ResultadoRegla:
    return _resultado(16, stop_reason == "refusal" or error_tras_reintentos,
                      "LLM_REFUSAL", "Revisión humana sin propuesta.")


def aplicar_reglas_previas(
    entrada: EntradaDenuncia, hallazgos_pii: list[str],
) -> tuple[EstadoAuxiliar | MarcaPipeline | None, list[ResultadoRegla]]:
    """Auditar RD-04 siempre y cortar las otras reglas en la primera aplicable."""
    resultados = [rd_04(entrada)]
    for regla, argumento in (
        (rd_02, entrada), (rd_03, entrada), (rd_06, hallazgos_pii),
        (rd_01, entrada), (rd_05, entrada),
    ):
        resultado = regla(argumento)
        resultados.append(resultado)
        if resultado.aplico:
            efecto = resultado.efecto
            if efecto in {e.value for e in EstadoAuxiliar}:
                return EstadoAuxiliar(efecto), resultados
            return MarcaPipeline(efecto), resultados
    return None, resultados


def aplicar_reglas_post(
    propuesta: PropuestaClasificacion, texto_seudonimizado: str, hechos: HechosExtraidos,
) -> tuple[PropuestaClasificacion, list[ResultadoRegla]]:
    """Corregir una copia y conservar toda evaluación en el orden prescrito."""
    copia = propuesta.model_copy(deep=True)
    resultado = rd_10(copia)
    resultados = [resultado]
    if resultado.aplico:
        copia = copia.model_copy(update={"decision": "PROCEDE_INVESTIGACION"})
    resultados.extend([rd_11(copia), rd_15(copia, texto_seudonimizado)])
    urgencia = rd_12(copia, texto_seudonimizado, hechos)
    resultados.append(urgencia)
    if urgencia.aplico:
        copia = copia.model_copy(update={"urgencia_resguardo": True})
    resultados.extend([rd_13(copia), rd_14(copia)])
    return copia, resultados
