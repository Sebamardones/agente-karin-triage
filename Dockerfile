# Una sola imagen para local, Heroku y cualquier destino posterior. Toda la
# configuración entra por variables de entorno (mitigación de RG-10: que el
# entorno publicado y el de destino no divergan).

# ---------- Etapa 1: dependencias ----------
FROM python:3.12-slim AS dependencias

# Versión fija de uv: el build no cambia si sale una versión nueva.
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app/backend

# Primero solo los manifiestos: así la capa de dependencias se reutiliza
# mientras no cambien, y un cambio de código no reinstala todo.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY backend/ ./
RUN uv sync --locked --no-dev


# ---------- Etapa 2: ejecución ----------
FROM python:3.12-slim AS ejecucion

# Usuario sin privilegios. Heroku ignora USER y asigna su propio UID, pero la
# imagen tiene que ser correcta en cualquier otro destino.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin karin

COPY --from=dependencias /opt/venv /opt/venv

WORKDIR /app

COPY --chown=karin:karin backend/ ./backend/
COPY --chown=karin:karin prompts/ ./prompts/
COPY --chown=karin:karin golden_set/ ./golden_set/
COPY --chown=karin:karin evals/ ./evals/

# KARIN_PROMPTS_DIR es obligatoria, no una comodidad.
#
# `services/llm.py` localiza el prefijo normativo subiendo por los directorios
# padres de su propio archivo. En el contenedor el paquete está instalado en el
# entorno virtual, no en `src/`, así que esa búsqueda no encuentra `prompts/` y
# toda llamada al modelo fallaría —y funcionaría perfecto en local, donde
# `uv sync` instala en modo editable. Esta variable cierra esa diferencia.
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    KARIN_PROMPTS_DIR=/app/prompts \
    PORT=8000

USER karin
EXPOSE 8000

# Heroku inyecta $PORT y hay que respetarlo. En local, el valor por omisión de
# arriba hace que el mismo comando sirva sin cambios.
CMD ["sh", "-c", "exec uvicorn karin_triage.api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
