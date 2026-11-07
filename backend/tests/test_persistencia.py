"""Pruebas de persistencia con datos sint?ticos y SQLite."""

from datetime import date

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from karin_triage.config import Ajustes
from karin_triage.config.ajustes import convertir_database_url
from karin_triage.models.tablas import (
    Base,
    Denuncia,
    Preclasificacion,
    UsoDiario,
    registrar_evento,
    verificar_cadena,
)


@pytest.fixture
def sesion():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def ajustes_env(monkeypatch):
    for campo in ("SESSION_SECRET", "DEMO_PASSWORD_ANALISTA", "DEMO_PASSWORD_SUPERVISOR"):
        monkeypatch.setenv("KARIN_" + campo, "solo-prueba-sintetica")
    monkeypatch.delenv("KARIN_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)


def denuncia(sesion):
    objeto = Denuncia(
        id_externo_dt="SINTETICO-1",
        tipo_ingreso="demo",
        fecha_denuncia=date(2026, 11, 7),
        empleador="EMPRESA_SINTETICA",
        sector_empleador="privado",
        texto_seudonimizado="[PERSONA_1]",
        hash_contenido="0" * 64,
        estado="REVISION_HUMANA",
    )
    sesion.add(objeto)
    sesion.flush()
    return objeto


def test_tablas(sesion):
    assert set(inspect(sesion.bind).get_table_names()) == {
        "denuncia",
        "preclasificacion",
        "revision_humana",
        "evento_auditoria",
        "uso_diario",
    }
    assert "texto_original" not in Denuncia.__table__.columns


def test_unicidad(sesion):
    caso = denuncia(sesion)
    sesion.add(Preclasificacion(denuncia_id=caso.id, version_pipeline="v1"))
    sesion.flush()
    sesion.add(Preclasificacion(denuncia_id=caso.id, version_pipeline="v1"))
    with pytest.raises(IntegrityError):
        sesion.flush()


def test_cadena_y_alteracion(sesion):
    caso = denuncia(sesion)
    eventos = [
        registrar_evento(sesion, caso.id, "demo", "REVISION", {"nivel": n}) for n in range(3)
    ]
    sesion.commit()
    assert verificar_cadena(sesion, caso.id)
    eventos[1].detalle = {"nivel": 99}
    sesion.commit()
    assert not verificar_cadena(sesion, caso.id)


def test_conversion_y_precedencia(ajustes_env, monkeypatch):
    assert convertir_database_url("postgres://host/db") == "postgresql+psycopg://host/db"
    assert convertir_database_url("sqlite://") == "sqlite://"
    monkeypatch.setenv("DATABASE_URL", "postgres://host/db")
    assert Ajustes().database_url == "postgresql+psycopg://host/db"
    monkeypatch.setenv("KARIN_DATABASE_URL", "sqlite://")
    assert Ajustes().database_url == "sqlite://"


def test_contador_por_fecha(sesion):
    uno = UsoDiario(fecha=date(2026, 11, 7), llamadas=1, usd=0.04)
    sesion.add_all([uno, UsoDiario(fecha=date(2026, 11, 8), llamadas=0, usd=0)])
    sesion.commit()
    uno.llamadas += 1
    uno.usd += 0.04
    sesion.commit()
    assert sesion.get(UsoDiario, date(2026, 11, 7)).usd == pytest.approx(0.08)
    assert sesion.get(UsoDiario, date(2026, 11, 8)).llamadas == 0


def test_migracion(ajustes_env, monkeypatch, tmp_path):
    url = "sqlite:///" + (tmp_path / "migracion.db").as_posix()
    monkeypatch.setenv("KARIN_DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(url)
    assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names())
    command.downgrade(config, "base")
    assert not set(Base.metadata.tables) & set(inspect(engine).get_table_names())
    engine.dispose()
