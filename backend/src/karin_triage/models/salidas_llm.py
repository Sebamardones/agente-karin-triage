"""Esquemas de intercambio; no ejecutan modelos ni herramientas."""

from typing import Literal

from pydantic import BaseModel, Field


class Cita(BaseModel):
    texto_literal: str
    fuente: Literal["denuncia", "normativa"]
    referencia: str | None = None


class HechosExtraidos(BaseModel):
    relacion_laboral_declarada: bool | None
    empleador_sector: Literal["PRIVADO", "PUBLICO", "NO_DETERMINADO"]
    conductas_descritas: list[str]
    reiteracion: Literal["UNICA", "REITERADA", "NO_DETERMINADO"]
    rol_persona_denunciada: Literal["EMPLEADOR", "JEFATURA", "PAR", "TERCERO", "NO_DETERMINADO"]
    indicios_riesgo_inmediato: list[str]
    efectos_declarados: list[str]
    citas: list[Cita]


class PropuestaClasificacion(BaseModel):
    informacion_suficiente: bool
    decision: Literal["PROCEDE_INVESTIGACION", "DERIVA_MEDIACION", "DESCARTADO"]
    tipo_conducta: list[Literal["ACOSO_LABORAL", "ACOSO_SEXUAL", "VIOLENCIA_TERCEROS"]]
    vulneracion_ddff: bool
    motivo_descarte: Literal[
        "NO_CONFIGURA_CONDUCTA", "SIN_RELACION_LABORAL", "DUPLICADA", "DESISTIMIENTO"
    ] | None
    urgencia_resguardo: bool
    confianza: float = Field(ge=0, le=1)
    justificacion: str
    citas: list[Cita]
    supuestos: list[str]
