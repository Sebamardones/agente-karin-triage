# Verificación del rediseño de la interfaz · 2026-11-08

Rama `entrega/codex-revision`. Ocho despliegues desde la release v13 (`4bd760f`):

| Release | Commit | Cambio |
|---|---|---|
| v14 | `3347eb4` | Identidad DT, franja de prototipo, limpieza de UX |
| v15 | `1de916b` | CSS versionado por contenido (caché del navegador) |
| v16 | `503e294` | Puesto de trabajo: bandejas por rol, cola y panel de decisión |
| v17 | `2664676` | Perfil «inspector», cápsulas e iconos |
| v18 | `8ceaf6b` | «Ingreso de caso» con campos reales y pie de página |
| v19 | `62d233c` | Menú, guía de bienvenida, animaciones y ajuste de botones |
| v20 | `5a68bc1` | Grilla común de encabezado y pie, cola y panel más limpios |
| v21 | `e775425` | Porcentaje del resumen sin cortes |

Evidencia de cada despliegue:
- `pytest -q` antes del commit: 266 → 273 → 280 → 283 pruebas aprobadas;
  `ruff check .` sin hallazgos.
- Revisión de `git diff --cached` sin claves.
- `heroku releases` con el commit esperado.
- `/salud` 200 y `/entrar` 200 sin sesión; las rutas nuevas
  (`/ingresos/nuevo`) redirigen al login sin sesión.
- Sin errores en los últimos 40 registros de Heroku.
- CSS publicado con la huella esperada.

Recorridos verificados en una copia local con SQLite, casos sintéticos y sin
clave de API (sin gasto):
- confirmar → aviso «pasó a Revisados» → apertura del siguiente caso;
- descarte con cita tomada de la selección → «Enviado a un supervisor» →
  validación del supervisor → «caso cerrado»;
- ingreso del sector público → seguimiento → apertura automática con RD-02,
  sin IA;
- teclado (`j`/`k`, `c`, `?`), móvil a 375 px sin desplazamiento horizontal y
  bordes alineados a 1440 px.

En producción se verificó la bandeja con la sesión del responsable después de
v14. Las releases siguientes se comprobaron sin sesión (rutas, recursos y
registros); no se registraron casos ni revisiones en producción para no gastar
créditos. El usuario de acceso cambió a `inspector_demo` en v17.

---

# Verificación actualizada tras EVALUACION_KARIN_TRIAGE

Fecha: 2026-11-07. Código desplegado: **2ed92a2**, Heroku **release v10**,
estado **succeeded**. [Árbol exacto](https://github.com/Sebamardones/agente-karin-triage/tree/2ed92a2).
Aplicación: https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/

## Evidencia nueva

- 253 pruebas aprobadas en 14,60 s; Ruff sin hallazgos.
- Build Docker y release correctos; migración aditiva 0002 para fundamentos
  de revisión humana, sin borrar casos ni revisiones existentes.
- Formulario de ficción accesible al inspector y bloqueado al supervisor.
- Un relato ficticio nuevo respondió al envío en 0,86 segundos, sin timeout;
  apareció con propuesta real de Claude y citas.
- El servidor rechazó un descarte humano sin fundamento con HTTP 422.
- Una revisión válida persistió y fue visible desde otra sesión con supervisor.
- Se solicitó una tanda nueva de once casos y no se registrarán revisiones sobre
  esa tanda durante las pruebas. Se conserva el historial previo.
- Consulta posterior de solo lectura: Postgres en migración 0002 y tanda
  completada con **11 casos, 0 revisiones y 11 pipelines tipificar_v3/reglas2**.
- Comparación real final: v3 decisiones 9/9, urgencia 9/9, positivos 3/3,
  citas 22/22 y salida validada sin reintento 9/9. Ver MEJORA_PROMPTS.md y
  evals/evidencia/; no se declara medición de JSON crudo.

Las comprobaciones públicas son HTTPS con cookies independientes, no inspección
visual en incógnito. La automatización del navegador no está disponible. La
grabación real del video y evidencia del límite de proyecto USD 20 en consola
Anthropic siguen pendientes del equipo/operador. No se cambió la clave.

## Comandos y archivos

```powershell
git clone --branch entrega/codex-revision https://github.com/Sebamardones/agente-karin-triage.git karin-correcciones
git switch -c correcciones/evaluacion-integral
uv run --python 3.12 --extra dev pytest -q -p no:cacheprovider --basetemp 'D:\AI Command Center\codex\tmp\evaluacion-final'
uv run --python 3.12 --extra dev ruff check .
uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v2.md
uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v3.md
git push origin HEAD:entrega/codex-revision
git push heroku HEAD:main
```

Los dos comandos de eval se ejecutaron mediante un wrapper local que usa en
memoria la clave existente de la plataforma, sin guardarla en el clon. Se
hicieron dos iteraciones por versión y se conservan los cuatro resultados.

Archivos de producto: API y plantillas, etiquetas, reglas RD-12/RD-15, nodos y
versión del pipeline, tabla RevisionHumana y migración 0002. Pruebas de API,
reglas, grafo, fuga de PII y métricas. Documentación: README, reglas del proyecto,
prompt maestro, ADR-020, trazabilidad, ficha MD/PDF y guion. Nuevo prompt v3,
golden set ampliado y evidencia JSON versionada.

Riesgos y pendientes: los descritos en CORRECCIONES_EVALUACION.md y ADR-020.
El precio de CLP 3.600.000 + IVA anual es una hipótesis comercial, no una venta
validada. La ficha identifica costos observados y presupuesto por separado.

---

## Registro histórico de la primera publicación (no es la versión vigente)

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
| Login inspector y supervisor | Correcto en sesiones separadas |
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

Usuarios de demostración: `inspector_demo` y `supervisor_demo`. El operador
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
