"""Persistencia portable entre SQLite y Postgres."""

import json
from datetime import UTC, date, datetime
from hashlib import sha256
from typing import ClassVar
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def ahora():
    return datetime.now(UTC).replace(tzinfo=None)


def identificador():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Denuncia(Base):
    # El texto original no se persiste: solo vive en memoria al seudonimizar.
    __tablename__ = "denuncia"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    id_externo_dt: Mapped[str] = mapped_column(String(200), unique=True)
    tipo_ingreso: Mapped[str] = mapped_column(String(100))
    fecha_denuncia: Mapped[date] = mapped_column(Date)
    fecha_ingesta: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    empleador: Mapped[str] = mapped_column(Text)
    sector_empleador: Mapped[str] = mapped_column(String(100))
    texto_seudonimizado: Mapped[str] = mapped_column(Text)
    hash_contenido: Mapped[str] = mapped_column(String(64))
    estado: Mapped[str] = mapped_column(String(100))


class Preclasificacion(Base):
    __tablename__ = "preclasificacion"
    __table_args__ = (UniqueConstraint("denuncia_id", "version_pipeline"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    denuncia_id: Mapped[str] = mapped_column(ForeignKey("denuncia.id"))
    version_pipeline: Mapped[str] = mapped_column(String(100))
    decision: Mapped[str | None] = mapped_column(String(100))
    estado_auxiliar: Mapped[str | None] = mapped_column(String(100))
    marcas_pipeline: Mapped[str] = mapped_column(Text, default="")
    tipo_conducta: Mapped[str] = mapped_column(Text, default="")
    vulneracion_ddff: Mapped[bool] = mapped_column(Boolean, default=False)
    urgencia_resguardo: Mapped[bool] = mapped_column(Boolean, default=False)
    motivo_descarte: Mapped[str | None] = mapped_column(String(100))
    confianza: Mapped[float | None] = mapped_column(Float)
    justificacion_y_citas: Mapped[list] = mapped_column(JSON, default=list)
    reglas_aplicadas: Mapped[str] = mapped_column(Text, default="")
    prioridad: Mapped[int] = mapped_column(Integer, default=0)
    tokens_entrada: Mapped[int] = mapped_column(Integer, default=0)
    tokens_salida: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    costo_usd: Mapped[float] = mapped_column(Float, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class RevisionHumana(Base):
    __tablename__ = "revision_humana"
    __table_args__ = (CheckConstraint("nivel IN (1, 2)"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identificador)
    preclasificacion_id: Mapped[str] = mapped_column(ForeignKey("preclasificacion.id"))
    funcionario: Mapped[str] = mapped_column(String(200))
    rol: Mapped[str] = mapped_column(String(100))
    nivel: Mapped[int] = mapped_column(Integer)
    decision_final: Mapped[str] = mapped_column(String(100))
    coincide_con_agente: Mapped[bool] = mapped_column(Boolean)
    comentario: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    __mapper_args__: ClassVar[dict] = {"version_id_col": version}


class EventoAuditoria(Base):
    __tablename__ = "evento_auditoria"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    denuncia_id: Mapped[str] = mapped_column(ForeignKey("denuncia.id"), index=True)
    actor: Mapped[str] = mapped_column(String(200))
    accion: Mapped[str] = mapped_column(String(100))
    # Solo metadatos estructurados; nunca texto libre de la denuncia.
    detalle: Mapped[dict] = mapped_column(JSON)
    hash_prev: Mapped[str] = mapped_column(String(64))
    hash_actual: Mapped[str] = mapped_column(String(64))
    ts: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class UsoDiario(Base):
    __tablename__ = "uso_diario"
    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    llamadas: Mapped[int] = mapped_column(Integer, default=0)
    usd: Mapped[float] = mapped_column(Float, default=0)


def _hash(prev, accion, detalle, ts):
    ordenado = json.dumps(detalle, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256((prev + accion + ordenado + ts.isoformat()).encode("utf-8")).hexdigest()


def registrar_evento(sesion, denuncia_id, actor, accion, detalle):
    """El llamador entrega metadatos sin contenido y controla la transacción."""
    sesion.flush()
    ultimo = sesion.scalar(
        select(EventoAuditoria)
        .where(EventoAuditoria.denuncia_id == denuncia_id)
        .order_by(EventoAuditoria.id.desc())
    )
    ts = ahora()
    prev = ultimo.hash_actual if ultimo else ""
    evento = EventoAuditoria(
        denuncia_id=denuncia_id,
        actor=actor,
        accion=accion,
        detalle=detalle,
        hash_prev=prev,
        hash_actual=_hash(prev, accion, detalle, ts),
        ts=ts,
    )
    sesion.add(evento)
    sesion.flush()
    return evento


def verificar_cadena(sesion, denuncia_id) -> bool:
    prev = ""
    for evento in sesion.scalars(
        select(EventoAuditoria)
        .where(EventoAuditoria.denuncia_id == denuncia_id)
        .order_by(EventoAuditoria.id)
    ):
        if evento.hash_prev != prev or evento.hash_actual != _hash(
            prev, evento.accion, evento.detalle, evento.ts
        ):
            return False
        prev = evento.hash_actual
    return True
