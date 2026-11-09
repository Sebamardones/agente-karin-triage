# Plan de entrega · auditoría contra la pauta

Fecha de la auditoría: 2026-11-08. Fuente: `pauta.pdf` (una página; todas las
citas son de la p. 1). Versión auditada: commit `4bd760f`, Heroku release
**v13** (`heroku releases -a karin-triage-grupo7`), que coincide con `HEAD` de
`entrega/codex-revision`.

> **Actualización del 9 de noviembre de 2026.** Las referencias `README.md:N`
> se ajustaron al README vigente, que creció al incorporar las cifras del
> informe DT con corte al 30 de junio de 2026, los 400 usuarios proyectados y
> el costo del despliegue nacional. El resto de la auditoría conserva el estado
> del commit `4bd760f`.

## Evidencia común

| Comando o fuente | Resultado |
|---|---|
| `python -m pytest -q` (venv temporal fuera del repo con `pip install -e ".[dev]"`; `uv` no está instalado en esta máquina) | `261 passed in 4.00s` |
| `ruff check .` (en `backend/`) | `All checks passed!` |
| `curl` sin cookies a `/` | `303 → /entrar`; `/entrar` responde `200` en 0,38 s |
| `gh repo view Sebamardones/agente-karin-triage` | `visibility: PUBLIC` |
| `heroku config` (solo nombres de variables) | `ANTHROPIC_API_KEY`, contraseñas demo y `KARIN_SESSION_SECRET` están como Config Vars; `KARIN_TOPE_USD_DIA=3`, `KARIN_TOPE_LLAMADAS_DIA=200` |
| `heroku ps` / `heroku addons` | 1 dyno web Basic activo; Postgres essential-0 |
| `git log --all -p \| grep -E 'sk-ant-…'` | Sin coincidencias. Búsqueda por patrón, no un escáner completo |
| Recorrido autenticado (navegador integrado, `inspector_demo`) | Bandeja con 23 casos, ficha de SINT-0002 y formulario `/demo/nuevo` |

No se creó ningún caso nuevo para no gastar créditos de Anthropic. La llamada
en vivo al modelo **no se probó hoy**; la evidencia de IA es la propuesta
guardada en los casos.

## Auditoría criterio por criterio

### Requisitos mínimos («Si falta uno, la nota máxima es 4,0»)

| Criterio (cita, p. 1) | Evidencia | Estado | Brecha | Acción propuesta |
|---|---|---|---|---|
| «El link público funciona al momento de corregir.» | `curl` → `/entrar` 200; release v13 activa | Cumple | Hoy funciona; nadie lo garantiza el día de la corrección | Verificación final en incógnito el 13 nov y no desplegar cambios riesgosos ese día |
| «El repositorio es accesible para el profesor.» | `gh repo view` → `PUBLIC` | Cumple | — | — |
| «Ninguna clave o contraseña dentro del repositorio.» | `.gitignore:2-4`; `.env.example:4,9-11` solo con marcadores; escaneo del historial sin coincidencias | Cumple | El escaneo es por patrón | Antes del cierre, revisar el historial con un escáner como gitleaks (es una dependencia nueva: requiere tu aprobación) |
| «Al menos una función usa IA generativa.» | `agent/nodos.py`; ficha de SINT-0002 con justificación generada y citas | Cumple | La llamada en vivo no se probó hoy | Probarla en la grabación del video (fase 3) |

### Entregables («Qué entregan»)

| Criterio (cita, p. 1) | Evidencia | Estado | Brecha | Acción propuesta |
|---|---|---|---|---|
| «URL pública del software funcionando.» | Igual que el requisito 1 | Cumple | — | — |
| «Repositorio GitHub con README (idea, cómo usarlo, arquitectura), `PROMPT_MAESTRO.md`, `/prompts` y golden set.» | `README.md:46` (idea), `:75` (uso), `:131` (arquitectura); `PROMPT_MAESTRO.md`; `prompts/` con 5 archivos; `golden_set/denuncias.jsonl` con 11 casos | Cumple | El README está desordenado: el enlace a los diagramas va antes de la presentación (`README.md:3`) y hay una sección de correcciones agregada al final (`:320`) | Reordenar el README (fase 4) |
| «Video demo de máximo 3 minutos: problema → demo en vivo → cómo lo construyeron.» | No existe; `docs/GUION_VIDEO.md` y `docs/CORRECCIONES_EVALUACION.md` lo declaran pendiente | No cumple | Falta el entregable completo | Fase 3 |
| «Ficha de negocio de 1 página en PDF: cliente, propuesta de valor, modelo de ingresos y costo mensual estimado de operar la app.» | `docs/FICHA_NEGOCIO.pdf`: `mdls` → 1 página; incluye las cuatro secciones | Cumple | Resuelto el 9 de noviembre: `README.md:72-73` enlaza el `.md` y el PDF | — |

### Escala de evaluación

| Criterio (cita, p. 1) | Evidencia | Estado | Brecha | Acción propuesta |
|---|---|---|---|---|
| **Idea de negocio, 20 pts.** Excelente: «Problema real y cliente concreto; la IA es clave en la propuesta de valor; modelo de ingresos y costo creíbles.» | `README.md:46-73`; ficha PDF con cifras del informe DT con corte al 30 de junio de 2026 (92.643 ingresos, 4.305/mes en el primer semestre de 2026), 400 usuarios proyectados, precio del piloto CLP 3.600.000 + IVA anual, costo de la demo USD 15/mes y costo nacional proyectado ≈ CLP 1.391.000/mes | Parcial | El problema y el cliente son sólidos. El ingreso se presenta solo como «hipótesis»: no hay escala (cuántas inspecciones), margen frente al costo ni el argumento de plazos (2 días hábiles y 30 días; `README.md:61-66`), que no aparece en la ficha | Reforzar la ficha: margen por inspección y plazos legales como propuesta de valor. La escala quedó resuelta el 9 de noviembre con la dotación de 400 usuarios y el costo nacional proyectado |
| **Software funcional, 25 pts.** Excelente: «Flujo completo de punta a punta, sin errores, fácil de usar por alguien externo.» | Recorrido en el navegador; `api/main.py:74`; `caso.html:10,23`; `_bandeja.html:4`; `login.html` | Parcial | El flujo funciona. Hay detalles que confunden a alguien externo: (1) la bandeja mezcla 23 casos de tandas antiguas con estados como «Revisión histórica · fundamento de descarte no capturado; usar nueva tanda»; (2) el historial muestra datos de prueba («Verificación técnica con caso sintético»); (3) el login no explica qué es la app ni dónde están las credenciales; (4) una propuesta de investigar muestra «Motivo de descarte: No corresponde» y las citas de denuncia dicen «Referencia: Sin referencia»; (5) jerga interna en la bandeja («procesados: 3, saltados: 8»); (6) los relatos sintéticos van sin tildes («companero», «tecnico») | Fase 2: rediseño DT y limpieza de textos. La bandeja muestra por defecto solo la tanda vigente (cambio de código, sin tocar el esquema). Las tildes del golden set requieren volver a medir v2/v3, con gasto de API: se deja para después |
| **Prompt engineering, 25 pts.** Excelente: «Prompt maestro completo; prompts versionados; golden set de 5+ casos con mejora medida entre versiones.» | `PROMPT_MAESTRO.md` (rol, objetivo, requisitos, restricciones, fases y criterios); `prompts/tipificar_v1..v3.md`; 11 casos; `docs/MEJORA_PROMPTS.md:9-24` (v2 → v3: citas 86 % → 100 %, válidas sin reintento 5/9 → 9/9, costo −25,3 %); 4 JSON en `evals/evidencia/` | Cumple | La mejora está bien documentada, pero queda lejos de la portada | Agregar al README una tabla corta v1 → v2 → v3 con enlace a la evidencia |
| **Despliegue y buenas prácticas, 20 pts.** Excelente: «URL estable; repo ordenado con README y Dockerfile; secretos en la plataforma; límite de gasto.» | URL estable (Basic, sin suspensión); `Dockerfile`; `heroku.yml`; Config Vars; `docs/LIMITE_GASTO.md:3` → **PENDIENTE**; no existe `docs/evidencia/` | Parcial | Falta el límite de gasto en la consola, con su captura. El repo está algo desordenado: README con capas agregadas y docs con secciones «Actualización» antepuestas a registros históricos | Tú configuras el límite y guardas la captura en `docs/evidencia/limite-gasto-consola.png`; yo actualizo los cinco documentos que lo citan. Ordenar el repo en la fase 4 |
| **Comunicación, 10 pts.** Excelente: «Video de 3 min claro y convincente; ficha precisa.» | No hay video; la ficha existe | No cumple | Sin video, el criterio queda en «Incompletos» (40 %) como máximo | Fase 3 y refuerzo de la ficha |

### Pasos de la pauta con verificación directa

| Criterio (cita, p. 1) | Evidencia | Estado |
|---|---|---|
| «Agreguen `CLAUDE.md` o `AGENTS.md` con las reglas del proyecto.» | Ambos en la raíz | Cumple |
| «una función de IA generativa con su prompt de sistema guardado en `/prompts`.» | `prompts/prefijo_normativo.md`, `extraer_hechos_v1.md`, `tipificar_v3.md` | Cumple |
| «documenten cómo mejoraron el prompt.» | `docs/MEJORA_PROMPTS.md` | Cumple |
| «Las claves van como secreto de la plataforma y con un límite de gasto configurado en la API de IA.» | Config Vars sí; límite de consola PENDIENTE | Parcial |
| «verifiquen que el link funcione desde un navegador en modo incógnito.» | Solo `curl` sin cookies; no hubo navegador en incógnito | No verificable |

## Estimación de puntaje (criterio propio, no oficial)

| Criterio | Hoy (estimado) | Tras el plan |
|---|---:|---:|
| Idea de negocio | 14–20 | 20 |
| Software funcional | 17,5 | 25 |
| Prompt engineering | 25 | 25 |
| Despliegue y buenas prácticas | 14 | 20 |
| Comunicación | 4 | 10 |
| **Total** | **≈ 75–81 (nota ≈ 5,1–5,6)** | **100 (7,0)** |

## Plan priorizado por impacto en la nota

| # | Ítem | Criterio y puntos en juego | Esfuerzo | Responsable | Fase |
|---|---|---|---|---|---|
| 1 | Grabar, narrar y exportar el video de ≤ 2:55 | Comunicación, hasta +6 | 6–8 h | Claude, con tus aprobaciones | 3 |
| 2 | Configurar el límite de USD 20 en la consola y guardar la captura | Despliegue, hasta +6 | 30 min tú + 20 min docs | Tú y luego Claude | — |
| 3 | Rediseño con la identidad DT, franja de prototipo académico y animaciones de estado | Software, hasta +7,5 (junto con 4) | 5–7 h | Claude | 2 |
| 4 | Limpieza de UX: bandeja solo con la tanda vigente, login con contexto, «No corresponde»/«Sin referencia», jerga de carga, historial de prueba | Software (junto con 3) | 2–3 h | Claude | 2 |
| 5 | Reforzar la ficha: plazos legales, escala, margen y regenerar el PDF de 1 página | Idea + Comunicación, hasta +6 | 1,5 h | Claude | 4 |
| 6 | Reordenar el README (título primero; enlaces a video, ficha PDF y demo; tabla v1 → v3; correcciones movidas a `docs/`) | Despliegue + Prompt | 1,5 h | Claude | 4 |
| 7 | Consistencia de `docs/`, `CLAUDE.md` y `PROMPT_MAESTRO.md` con el código | Despliegue (repo ordenado) | 2 h | Claude | 4 |
| 8 | Escaneo de secretos con herramienta dedicada | Requisito mínimo (riesgo) | 20 min | Claude, si apruebas la dependencia | 4 |
| 9 | Verificación final en incógnito y del enlace el 13 nov | Requisito mínimo | 15 min | Tú o Claude | Cierre |
| 10 | Tildes en los relatos del golden set y nueva medición v2/v3 | Software (detalle) | 1 h + gasto de API | Pendiente de tu decisión | Opcional |

Orden de ejecución, porque decidiste que el rediseño va antes de grabar:
3 y 4 → despliegue (con tu aprobación) → 1 → 5, 6 y 7 → 9. El ítem 2
puedes hacerlo en paralelo cuando quieras.

## Decisiones abiertas

- Ocultar las tandas antiguas: ¿solo un filtro de la bandeja (sin tocar la
  base) o archivarlas? Archivar podría exigir cambios de esquema y requiere tu
  aprobación.
- El ítem 10 gasta créditos de Anthropic; solo con tu aprobación.
- `pauta.pdf` está sin versionar en la raíz: ¿se agrega al repo o queda fuera?

## Estado al cierre del 8 de noviembre

| # | Ítem | Estado | Evidencia |
|---|---|---|---|
| 1 | Video | Pendiente (fase 3) | — |
| 2 | Límite de gasto en la consola | Pendiente del responsable | `docs/LIMITE_GASTO.md` sigue en PENDIENTE |
| 3–4 | Rediseño y experiencia de uso | Hecho y desplegado (v14–v21) | `docs/VERIFICACION_PUBLICA.md`, ADR-021, `docs/capturas/` |
| 5 | Refuerzo de la ficha | Pendiente (fase 4) | Solo se actualizó el texto del ingreso de caso |
| 6–7 | README y consistencia de documentos | Actualizados con los cambios del día | Este commit |
| 8 | Escaneo de secretos con herramienta dedicada | Pendiente (requiere aprobar una dependencia) | — |
| 9 | Verificación final en incógnito | Pendiente (13 nov) | — |
| 10 | Tildes del golden set | No iniciado (gasta API) | — |

Cambio para la entrega: el usuario de acceso es `inspector_demo` (antes
`analista_demo`); la contraseña no cambió. Hay que informarlo en la plataforma
del curso.
