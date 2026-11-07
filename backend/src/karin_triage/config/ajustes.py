"""Ajustes; la clave de Anthropic pertenece exclusivamente al SDK."""

import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def convertir_database_url(url: str) -> str:
    """Adapta el esquema histórico de Heroku al controlador psycopg."""
    return (
        url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://")
        else url
    )


class AjustesNucleo(BaseSettings):
    """Lo que necesitan el grafo y el cliente del modelo.

    Deliberadamente **no** incluye los secretos de la sesion web ni las
    contrasenas de demostracion. Si los incluyera, instanciar los ajustes dentro
    de una llamada al modelo fallaria con un error de validacion en cualquier
    entorno donde esas variables no esten definidas, por ejemplo al correr el
    runner de evaluaciones. El sintoma seria un fallo de configuracion
    disfrazado de fallo del modelo.
    """

    model_config = SettingsConfigDict(env_prefix="KARIN_")
    database_url: str = "sqlite+pysqlite:///./karin_dev.db"
    modelo: str = "claude-sonnet-5"
    tope_llamadas_dia: int = 200
    tope_usd_dia: float = 3.0

    def model_post_init(self, context):
        if "database_url" not in self.model_fields_set and os.getenv("DATABASE_URL"):
            self.database_url = convertir_database_url(os.environ["DATABASE_URL"])


class Ajustes(AjustesNucleo):
    """Agrega lo que solo necesita la aplicacion web."""

    session_secret: SecretStr
    demo_password_analista: SecretStr
    demo_password_supervisor: SecretStr
