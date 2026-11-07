"""Alembic usa exclusivamente la URL de los ajustes."""

from alembic import context
from sqlalchemy import create_engine, pool

from karin_triage.config import Ajustes
from karin_triage.models.tablas import Base

url = Ajustes().database_url
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
