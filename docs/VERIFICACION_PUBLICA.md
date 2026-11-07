# Despliegue y verificación pública - KARIN triage

Fecha: 2026-11-07. Objetivo: publicar el prototipo y comprobar el flujo público
con IA activa y datos sintéticos, sin publicar credenciales.

## Destinos y versión

- Aplicación: https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/
- Repositorio público: https://github.com/Sebamardones/agente-karin-triage
- Rama: `entrega/codex-revision`.
- Commit de código desplegado: `5175195`.
- Heroku release v6: `succeeded`, confirmado por CLI.
- Un dyno Basic y Postgres Essential-0. Costo base aprobado: USD 12/mes,
  más inferencia. Se conserva la clave Anthropic existente por instrucción
  expresa del operador. No se imprime ni se versiona.

## Resultados

| Comprobación | Resultado |
|---|---|
| Docker construido en Heroku | Correcto |
| Migración Alembic y release | Correctos |
| Dyno web | Activo, Basic |
| GET HTTPS `/salud` | `estado=ok` |
| Acceso sin cookie a `/` | Redirección a `/entrar` |
| Login analista y supervisor | Correcto en sesiones separadas |
| Carga sintética después de la corrección | Respuesta inmediata, sin 503 |
| Casos guardados en Postgres | 8 |
| Propuestas con citas | 6; otros dos casos tienen estado auxiliar |
| Uso de IA | Registro de uso presente y propuestas reales con citas |
| Corrección de una propuesta | Guardada y visible en otra sesión |
| Persistencia al redesplegar | Los ocho casos y la primera revisión se conservaron |
| Suite completa final | 231 pruebas aprobadas, 7,18 s |
| Ruff | Sin hallazgos |

Verificación pública mediante peticiones HTTPS y sesiones con cookies nuevas.
No se efectuó una inspección visual con navegador en incógnito: el host de
automatización de navegador no estaba disponible. Esa comprobación visual
manual sigue pendiente para la entrega del curso.

## Corrección necesaria durante el despliegue

La carga original de ocho casos superó el tiempo límite del router Heroku y
respondió 503 aunque el servidor seguía procesando. Se movió a BackgroundTasks
con una sesión de base de datos propia; la bandeja muestra contadores y un
enlace para actualizar. Un lock evita cargas simultáneas dentro del proceso.
El nuevo comportamiento fue comprobado en la URL pública.

Archivos de producto cambiados: `backend/src/karin_triage/api/main.py`,
`backend/src/karin_triage/api/plantillas/bandeja.html`,
`backend/tests/test_api.py`, `README.md` y
`docs/adr/ADR-018-carga-demo-segundo-plano.md`.

## Comandos principales ejecutados

```powershell
heroku apps:create karin-triage-grupo7 --stack container --json
heroku addons:create heroku-postgresql:essential-0 --app karin-triage-grupo7
git push heroku HEAD:main
heroku ps:resize web=basic --app karin-triage-grupo7
heroku ps:scale web=1 --app karin-triage-grupo7
heroku ps --app karin-triage-grupo7
heroku releases:info --app karin-triage-grupo7 --json
uv run --python 3.12 --extra dev pytest -q -p no:cacheprovider --basetemp 'D:\AI Command Center\codex\tmp\karin-final-tests'
uv run --python 3.12 --extra dev ruff check .
git push origin entrega/codex-revision
```

La configuración de secretos se realizó mediante la API de Heroku, con valores
solo en memoria. Los verificadores locales iniciaron sesión, solicitaron la
carga, consultaron propuestas y enviaron correcciones de casos sintéticos;
no están en el repositorio porque pertenecen al entorno local del operador.

## Acceso y pendientes

Usuarios de demostración: `analista_demo` y `supervisor_demo`. El operador
consulta las contraseñas en Settings / Config Vars de la aplicación Heroku,
en `KARIN_DEMO_PASSWORD_ANALISTA` y `KARIN_DEMO_PASSWORD_SUPERVISOR`, y las
entrega al profesor por la plataforma del curso.

La carga en segundo plano y sus contadores no sobreviven a reinicios; los
casos ya guardados sí. Volver a solicitarla omite los casos persistidos.
La coordinación se limita a un proceso: mantener un dyno y un worker.

Persisten los límites de evaluación documentados en MEJORA_PROMPTS.md. No se
afirma que todas las metas del prompt maestro estén cumplidas. Falta comprobar
visualmente el flujo en incógnito, entregar el video y comprobar el límite de
proyecto en la consola Anthropic. Se configuraron topes en código de USD 3 y
200 llamadas por día. La aceptación formal de fases corresponde al operador.
