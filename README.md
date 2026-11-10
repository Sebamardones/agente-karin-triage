# agente-karin-triage

Pre-clasificación asistida de denuncias de Ley Karin (Ley 21.643) para
funcionarios de la Dirección del Trabajo.

**El agente propone. Una persona decide.**

**Aplicación pública:** https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/

Acceso con `inspector_demo` y `supervisor_demo`. Las contraseñas se entregan por
la plataforma del curso; no están en este repositorio. Solo casos sintéticos.

## Entregables

| Entregable | Dónde |
|---|---|
| Software funcionando | [URL pública](https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/) · [cómo usarlo](#cómo-usar-la-aplicación) |
| Ficha de negocio (1 página) | [`docs/FICHA_NEGOCIO.pdf`](docs/FICHA_NEGOCIO.pdf) · [versión extendida](docs/FICHA_NEGOCIO.md) · [caso ampliado](https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/estaticos/ficha-negocio.html) |
| Video demo (≤ 3 min) | [Ver el video en Google Drive](https://drive.google.com/file/d/1Jx_mQYaCTQnniF7c6qNfBF4t7PFV-HgJ/view?usp=share_link) (2:32) · guion y montaje: [`docs/GUION_VIDEO.md`](docs/GUION_VIDEO.md) |
| Prompt maestro | [`PROMPT_MAESTRO.md`](PROMPT_MAESTRO.md) |
| Prompts versionados | [`prompts/`](prompts/) · [mejora medida v1 → v3](#mejora-medida-de-los-prompts) |
| Golden set | [`golden_set/denuncias.jsonl`](golden_set/denuncias.jsonl), 11 casos sintéticos |
| Reglas del proyecto | [`CLAUDE.md`](CLAUDE.md) · [`AGENTS.md`](AGENTS.md) |
| Despliegue | [`Dockerfile`](Dockerfile) · [`heroku.yml`](heroku.yml) · [control de gasto](docs/LIMITE_GASTO.md) |

> **Estado de este repositorio.** Es la *edición de entrega* del Proyecto Final:
> un prototipo público que opera con denuncias **sintéticas**. El piloto
> institucional —ClaveÚnica, GKE, Langfuse, datos reales— está documentado en
> [Hoja de ruta](#hoja-de-ruta-hacia-el-piloto) y deliberadamente **no** forma
> parte de este código. El porqué de ese recorte está en
> [`docs/adr/ADR-017`](docs/adr/ADR-017-edicion-entrega-heroku.md).

---

## Integrantes

| Nombre |
|---|
| Edith Seguel |
| Nicolás Mores |
| Sebastián Mardones |

Universidad Adolfo Ibáñez · Certificado en Prompt Engineering · Grupo 7

## La idea

La Dirección del Trabajo registró **92.643 ingresos** asociados a denuncias por
acoso laboral, acoso sexual y violencia en el trabajo entre el 1 de agosto de
2024 y el 30 de junio de 2026. Solo el primer semestre de 2026 sumó 25.830:
unas **4.305 al mes**. De esos 92.643 registros, **32.565 (35%)** fueron
clasificados para continuar como Ley Karin, **48.505 (52%)** fueron derivados o
cerrados por no corresponder a esa vía y 11.573 (12%) seguían pendientes de
clasificación.[^informe]

La plataforma está pensada para **400 usuarios**: 200 inspectores dedicados
exclusivamente a la recepción de casos Ley Karin y 200 funcionarios con
dedicación no exclusiva, entre ellos los supervisores.

Esa etapa de pre-clasificación es obligatoria, ya existe, y hoy se hace a mano
contra plazos que no admiten holgura: **2 días hábiles** para pedir medidas de
resguardo (art. 211-B bis del Código del Trabajo) y **30 días** para concluir la
investigación (art. 211-C). Si la Inspección no se pronuncia en 30 días sobre un
informe interno, **se tienen por válidas las conclusiones del empleador**: el
atraso administrativo no es neutro, favorece al empleador investigado.

Este sistema toma cada denuncia y entrega al funcionario una propuesta fundada
en citas literales: qué conducta se configura, si corresponde investigar,
derivar a mediación o descartar, y si hay urgencia de medidas de resguardo. El
funcionario confirma o corrige, y lo que corrige queda registrado.

La ficha de una página está en [`docs/FICHA_NEGOCIO.pdf`](docs/FICHA_NEGOCIO.pdf)
y el caso de negocio completo, con precio del piloto por unidad de recepción,
margen, consumo mensual a 1.581 casos y costo del despliegue nacional, en [`docs/FICHA_NEGOCIO.md`](docs/FICHA_NEGOCIO.md).

## Cómo usar la aplicación

### En la URL pública

1. Abre la URL de la demostración (está en la entrega del curso) en una ventana
   de incógnito.
2. Entra con uno de los dos usuarios de demostración. **Las contraseñas van en
   la plataforma del curso, nunca en este repositorio.**
   - `inspector_demo` — ingresa casos y hace la primera revisión: confirma,
     corrige o descarta la propuesta del agente.
   - `supervisor_demo` — valida los descartes y las excepciones a RD-10 en la
     bandeja «Por validar».
3. Al entrar se abre una guía de tres pasos (una vez por sesión; se reabre desde
   «Cómo usar» en el menú). La bandeja no preselecciona ningún caso.
4. A la izquierda está la **cola**: bandejas por estado (Por revisar, Esperando
   supervisor, Revisados, Cerrados) y tarjetas con los urgentes arriba. Para
   tener casos, usa «Más acciones → Crear tanda nueva» o registra uno en
   **«Ingreso de caso»** (`/ingresos/nuevo`), con tipo de ingreso, fecha,
   empleador, sector y relato. Un ingreso del sector público se deriva por
   RD-02 sin llamar a la IA.
5. Al elegir un caso, el panel muestra el **veredicto** del agente, el relato
   con las **citas literales resaltadas**, el **recorrido** por las reglas duras
   y la justificación.
6. Decide con **Confirmar propuesta**, **Corregir** o **Descartar**. El
   descarte pide motivo, comentario y una cita que se toma seleccionando la
   frase en el relato, y pasa a un supervisor distinto. Tras cada decisión se
   abre el siguiente caso y un aviso indica a qué bandeja pasó.

Todos los datos son sintéticos. No hay ninguna denuncia real en este sistema.
La franja superior y el pie de página lo declaran en todas las pantallas.

La carga del golden set se ejecuta en segundo plano: pulsar una vez y usar
«Actualizar bandeja» para ver el avance. Los casos procesados se conservan en
Postgres. La tarea y sus contadores viven en un único proceso web; si el dyno
se reinicia, volver a solicitar la carga omite los casos ya guardados. Esta
implementación se limita a un dyno y un worker, sin cola durable distribuida.

### En local

```bash
# Backend, con uv
cd backend
uv sync --extra dev

# Pruebas
uv run --extra dev pytest -q
uv run --extra dev ruff check .

# Variables de entorno
cp ../.env.example ../.env   # y completa ANTHROPIC_API_KEY

# Servidor
uv run uvicorn karin_triage.api.main:app --reload
```

### Con Docker

```bash
docker build -t karin-triage .
docker run --rm -p 8000:8000 --env-file .env karin-triage
```

## Arquitectura

**Diagramas:** [atlas HTML público](https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/estaticos/diagramas-karin-triage.html)
· [SVG y fuentes Mermaid](docs/diagramas/README.md). Para presentar el negocio:
[contexto](docs/diagramas/karin-1.svg) y [revisión humana](docs/diagramas/karin-8.svg).
El atlas distingue implementación, evidencia y funcionalidades futuras.

### El flujo de un caso

```mermaid
flowchart TD
    S([ingreso]) --> N1["ingestar_y_validar"]
    N1 --> RP{"reglas_previas<br/>RD-01 a RD-05"}
    RP -->|"sector público"| AUX2["DERIVAR_OTRA_INSTITUCION"]
    RP -->|"informe interno"| FA["FUERA_DE_ALCANCE"]
    RP -->|"faltan campos"| AUX1["REQUIERE_ANTECEDENTES"]
    RP -->|"ok"| N2["seudonimizar"]
    N2 --> PII{"control_pii_residual<br/>RD-06"}
    PII -->|"PII detectada"| HUM
    PII -->|"limpio"| N3["extraer_hechos<br/>LLM"]
    N3 --> N5["tipificar_y_proponer<br/>LLM + prefijo cacheado"]
    N5 --> N6{"validar_salida<br/>esquema + citas literales"}
    N6 -->|"inválida · 1 reintento"| N5
    N6 -->|"válida"| N7["reglas_duras_post<br/>RD-10 a RD-15"]
    N3 -.->|"refusal o error"| HUM
    N5 -.->|"refusal o error"| HUM
    N7 --> N8["calcular_ruta<br/>prioridad"]
    N8 --> HUM[["cola_revision_humana"]]
    AUX1 --> HUM
    AUX2 --> HUM
    FA --> HUM
    HUM --> N9["registrar_decision_auditada"]
    N9 --> E([fin])
```

**Toda ruta termina en `cola_revision_humana`.** No hay ningún camino por el que
un caso salga del sistema sin pasar por una persona. Eso no es una
característica del flujo: es la restricción de diseño de la que se derivan las
demás.

### Las tres capas, y por qué están en ese orden

1. **Reglas duras deterministas, antes del modelo** (`core/reglas.py`). Lo que
   no admite interpretación no se le pregunta a un LLM. Sector público, informe
   interno, registro incompleto y régimen anterior se resuelven en código, con
   un test por regla. Un caso del sector público **nunca llega al modelo**: su
   costo de inferencia es cero.
2. **Seudonimización, antes del modelo** (`services/seudonimizador.py`).
   Nombres, RUT, correos, teléfonos y direcciones se sustituyen por tokens. Un
   detector vuelve a escanear el resultado y, si encuentra algo,
   **corta el flujo sin llamar al modelo** (RD-06).
3. **Dos nodos LLM acotados** (`agent/nodos.py`). Uno extrae hechos, el otro
   tipifica y propone. Salida validada con Pydantic, citas verificadas carácter
   por carácter, y reglas duras posteriores que pueden corregir al modelo.

### La regla que más importa

**RD-10.** Si el modelo propone derivar a mediación un caso que incluye acoso
sexual, el código fuerza `PROCEDE_INVESTIGACION` y deja constancia del error.

El fundamento es el artículo 211-D inciso final, que remite al artículo 486
*«con excepción de lo consagrado en el inciso sexto respecto a las conductas
establecidas en la letra a) del artículo 2»*. El inciso sexto es el de la
mediación previa, y la letra a) es el acoso sexual. Enviar un caso de acoso
sexual a mediación obligaría a la persona afectada a negociar con quien la
acosó.

Es también uno de los once casos del golden set, y una de las dos metas que **no
se compensan**: si una versión del prompt falla aquí, esa versión no se publica.

### Prompts

Los prompts versionados están en [`prompts/`](prompts/):

| Archivo | Qué es |
|---|---|
| `prefijo_normativo.md` | Bloque de sistema **cacheado**, estable byte a byte, compartido por los dos nodos. Contiene el texto literal de las normas y la matriz de criterios |
| `extraer_hechos_v1.md` | Nodo 1. Extrae hechos sin clasificar |
| `tipificar_v1.md` | Nodo 2, **línea base**. Rol, delimitación de datos, criterios y esquema, sin ejemplos |
| `tipificar_v2.md` | Nodo 2. Procedimiento de decisión ordenado, tres ejemplos resueltos, guía de citas y antipatrones |
| `tipificar_v3.md` | Nodo 2, **en uso** (`agent/nodos.py`). Separa urgencia de gravedad, distingue represalia sindical sin acoso y limita las citas a fragmentos de la denuncia |

#### Mejora medida de los prompts

Mismo runner y mismo golden set en cada comparación. Detalle, límites de la
medición y reproducción en [`docs/MEJORA_PROMPTS.md`](docs/MEJORA_PROMPTS.md);
JSON de las corridas en [`evals/evidencia/`](evals/evidencia/).

| Métrica | v1 | v2 | v3 |
|---|---:|---:|---:|
| Decisión final correcta | 6/6 | 6/6 · 9/9 | 9/9 |
| Citas verificadas contra su fuente | — | — · 25/29 (86 %) | **22/22 (100 %)** |
| Salida y citas válidas sin reintento | 0/6 | 1/6 · 5/9 | **9/9** |
| Acoso sexual enviado a mediación | 0 | 0 · 0 | 0 |
| Falsos descartes | 0 | 0 · 0 | 0 |
| Costo estimado de la corrida, USD | 0,1942 | 0,1889 · 0,2142 | **0,1600** |

v1 → v2 se midió con ocho casos (seis con LLM); v2 → v3, con once (nueve con
LLM) y un runner corregido que verifica cada cita contra su fuente. En la
columna v2, el primer valor es de la comparación con v1 y el segundo, de la
comparación con v3. v3 costó 25,3 % menos que v2, con cuatro llamadas menos. Es
una corrida por versión: no es una garantía estadística.

El prefijo normativo va como primer bloque de `system` con `cache_control` y TTL
de una hora, y es **idéntico** en los dos nodos para que ambos lean del mismo
caché. El prompt específico de cada nodo va en un segundo bloque. Por eso el
prefijo no puede contener fechas, identificadores ni contadores: un solo byte
distinto invalida el caché, y se nota en `usage.cache_read_input_tokens`.

### Estructura del repositorio

```text
.
├── PROMPT_MAESTRO.md          # prompt de construcción del proyecto
├── CLAUDE.md · AGENTS.md      # reglas inviolables
├── Dockerfile · heroku.yml
├── prompts/                   # prompts de sistema versionados
├── golden_set/denuncias.jsonl # 11 casos sintéticos con salida esperada
├── evals/                     # runner y métricas por versión de prompt
├── backend/
│   ├── pyproject.toml
│   ├── src/karin_triage/
│   │   ├── core/              # taxonomía y reglas duras · sin LLM
│   │   ├── services/          # seudonimizador, cliente del modelo
│   │   ├── models/            # Pydantic y SQLAlchemy
│   │   ├── agent/             # grafo y nodos
│   │   └── api/               # FastAPI: puesto de trabajo, ingreso de caso, login
│   │       ├── presentacion.py    # bandejas, citas resaltadas y recorrido (solo lectura)
│   │       ├── plantillas/        # Jinja2: bandeja.html (puesto), caso.html (panel), nuevo.html (ingreso)
│   │       └── estaticos/         # estilo.css, interaccion.js, htmx, logo y cinta DT
│   └── tests/                 # reglas · seudonimización · fuga de PII · inyección · interfaz
└── docs/
    ├── ARQUITECTURA.md        # arquitectura del piloto (hoja de ruta)
    ├── FICHA_NEGOCIO.md · FICHA_NEGOCIO.pdf
    ├── generar_ficha_pdf.py   # regenera el PDF de una página
    ├── CORRECCIONES_EVALUACION.md
    ├── MEJORA_PROMPTS.md
    ├── GUION_VIDEO.md
    ├── plan-entrega.md        # auditoría contra la pauta y plan priorizado
    ├── plan-diseno.md         # identidad DT, HIG, animaciones y accesibilidad
    ├── plan-interaccion.md    # puesto de trabajo: bandejas, panel y decisión
    ├── capturas/              # antes y después del rediseño
    ├── diagramas/
    ├── adr/
    └── INFORME_ARQUITECTURA_Y_AUDITORIA.md
```

La interfaz es HTML renderizado en el servidor con Jinja2 y htmx, sin
frameworks de frontend ([ADR-016](docs/adr/ADR-016-bandeja-servidor.md)). Las
decisiones del puesto de trabajo y del perfil «inspector» están en
[ADR-021](docs/adr/ADR-021-puesto-de-trabajo.md). Suite actual: **283 pruebas**
(`uv run --extra dev pytest -q` en `backend/`).

## Seguridad y datos

- **Solo datos sintéticos.** No hay ninguna denuncia real en el repositorio ni
  en la demostración.
- **Ninguna clave en el repositorio ni en su historial.** Secretos por variable
  de entorno y, en Heroku, por `heroku config:set`.
- **El texto de la denuncia es dato, nunca instrucción.** Va delimitado en
  `<denuncia>` y el modelo no tiene herramientas. Hay un caso del golden set que
  intenta una inyección explícita.
- **Control de gasto en tres capas** ([detalle y procedimiento](docs/LIMITE_GASTO.md)):
  1. Límite mensual de USD 20 de la organización en la consola de Anthropic,
     configurado el 9 de noviembre de 2026
     ([captura](docs/evidencia/limite-gasto-consola.png)).
  2. Tope diario de llamadas y de dólares en el código. Al alcanzarlo, el caso se
     marca `PRESUPUESTO_AGOTADO` y pasa a cola manual.
  3. Si el proveedor rechaza la llamada (límite de la consola, cuota o caída),
     el caso se guarda sin propuesta en la cola manual con RD-16; no se pierde.

## Hoja de ruta hacia el piloto

Todo lo siguiente está diseñado en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)
y **no** está implementado aquí, por decisión explícita:

| Pieza | Por qué queda fuera de esta edición |
|---|---|
| **ClaveÚnica (OIDC)** | Un evaluador externo no podría entrar. Se reemplaza por login de demostración con roles |
| **RLS por inspección en Postgres** | El piloto es de una sola inspección; no se puede demostrar con dos usuarios de prueba |
| **GKE Autopilot en `southamerica-west1`** | Un solo servicio en Heroku alcanza para la demostración, con la misma imagen Docker |
| **Cloud KMS** | Solo se necesita para cifrar la tabla de re-identificación de datos reales |
| **Langfuse *self-hosted*** | Se reemplaza por logs estructurados. Operar ClickHouse excede al equipo (riesgo RG-11) |
| **Ingesta horaria desde Mi DT** | Requiere acuerdo de integración. Se reemplaza por carga manual del golden set |
| **Set histórico real y gold set con doble etiquetado** | Requiere autorización escrita del encargado de datos de la DT |
| **EIPD (Ley 21.719)** | Solo exigible al procesar datos reales |
| **Modo sombra** | Requiere el piloto en una inspección |
| **Bandeja React + Vite + TS** | Ver [`docs/adr/ADR-016`](docs/adr/ADR-016-bandeja-servidor.md) |
| **Validación jurídica de la matriz de criterios** | La matriz está `PROVISIONAL`: el dueño del criterio es el sponsor, no un abogado de la DT. Mientras siga así, el *gate* al modo asistido queda bloqueado |

## Limitaciones conocidas

- **La matriz de criterios no tiene validación jurídica.** Es el riesgo RG-01 y
  la razón por la que ningún caso avanza sin revisión humana.
- **La seudonimización de esta edición es por expresiones regulares y
  heurística de nombres propios**, sin reconocimiento de entidades. Es
  deliberadamente conservadora: prefiere un token de más a un nombre de menos.
- **El umbral de confianza (0,75) no está calibrado con datos.** Es un valor
  inicial; la calibración requiere el set histórico.
- **`claude-sonnet-5` en los dos nodos.** `claude-opus-5` queda detrás de una
  variable de entorno apagada.
- Tres afirmaciones sobre la API de Anthropic que contenía el documento original
  resultaron incorrectas al verificarlas, incluida **un identificador de modelo
  que no existe**. Están corregidas y documentadas en
  [`docs/adr/ADR-003`](docs/adr/ADR-003-sdk-anthropic.md).

## Correcciones de la evaluación del equipo

Las observaciones de la evaluación interna y cómo se cerró cada una están en
[`docs/CORRECCIONES_EVALUACION.md`](docs/CORRECCIONES_EVALUACION.md).

---

[^informe]: Dirección del Trabajo, *Informe estadístico semestral sobre
denuncias en materias de la Ley N.° 21.643 con corte al 30 de junio de 2026.
Período acumulado: 1 de agosto de 2024 a 30 de junio de 2026*, agosto de 2026.
<https://www.dt.gob.cl/portal/1626/articles-129626_archivo_01.pdf>. Reemplaza las cifras del informe anterior
(<https://www.dt.gob.cl/portal/1626/articles-128897_archivo_01.pdf>), que la DT
ajustó por consolidación de registros.
