# Diagramas actualizados de KARIN Triage
Corte de código: `056733e` · 7 de noviembre de 2026.
La arquitectura original de octubre se conserva como antecedente en la carpeta local histórica. Estas vistas describen la edición publicada, no el piloto institucional.
| # | Diagrama | Uso recomendado |
|---|---|---|
| 1 | [Contexto de la edición publicada](karin-1.svg) | Ficha de negocio y README |
| 2 | [Grafo LangGraph realmente implementado](karin-2.svg) | GitHub · arquitectura |
| 3 | [Secuencia de un caso y una revisión](karin-3.svg) | GitHub · operación y revisión |
| 4 | [Modelo de datos implementado](karin-4.svg) | GitHub · datos y auditoría |
| 5 | [Despliegue de la edición pública](karin-5.svg) | GitHub; anexo técnico comercial |
| 6 | [Flujo real de verificación y publicación](karin-6.svg) | GitHub · reproducibilidad |
| 7 | [Evidencia disponible y siguiente etapa](karin-7.svg) | GitHub; anexo de la ficha ampliada |
| 8 | [Revisión humana: responsabilidades y estados](karin-8.svg) | Ficha de negocio y README |

## 1. Contexto de la edición publicada

![Contexto de la edición publicada](karin-1.svg)

**Uso:** Ficha de negocio y README. Explica quién usa el servicio, qué prepara la IA y dónde se conserva la responsabilidad humana. Es el mejor diagrama para la propuesta de valor.

**Sustituye la vista antigua de:** GCP, ClaveÚnica, ingesta horaria, React, RLS y Langfuse.

```mermaid
flowchart LR
  A[Inspector demo] --> UI[FastAPI + Jinja2 + HTMX]
  S[Supervisor demo] --> UI
  I[Formulario ficticio y golden set] --> G[BackgroundTasks + LangGraph]
  UI --> G
  G --> P[Reglas + seudonimización + PII]
  P --> C[API Anthropic: hechos y tipificación]
  G --> DB[(Postgres Heroku)]
  UI --> DB
```

## 2. Grafo LangGraph realmente implementado

![Grafo LangGraph realmente implementado](karin-2.svg)

**Uso:** GitHub · arquitectura. Permite contrastar nodos, ramas y reintento directamente con grafo.py. No conviene incorporarlo completo al PDF de una página.

**Sustituye la vista antigua de:** Recuperación de normativa, interrupt() y checkpointer.

```mermaid
flowchart TD
  A[ingestar_y_validar] --> B[reglas_previas]
  B -->|sin corte| C[seudonimizar]
  B -->|estado o marca| I[calcular_ruta]
  C --> D[control_pii_residual]
  D -->|PII| I
  D -->|sin hallazgos| E[extraer_hechos]
  E -->|correcto| F[tipificar_y_proponer]
  E -->|refusal o presupuesto o error| I
  F -->|correcto| G[validar_salida]
  F -->|refusal o presupuesto o error| I
  G -->|primer fallo| F
  G -->|continuar| H[reglas_duras_post]
  H --> I --> J[persistir] --> K[END]
  K -. consulta posterior por API .-> L[Revisión humana fuera del grafo]
```

## 3. Secuencia de un caso y una revisión

![Secuencia de un caso y una revisión](karin-3.svg)

**Uso:** GitHub · operación y revisión. Aclara por qué la petición HTTP regresa antes de terminar la IA y dónde ocurre el commit. Útil para revisar fallos y continuidad.

**Sustituye la vista antigua de:** CronJob, tabla job, SKIP LOCKED y mapa cifrado con KMS.

```mermaid
sequenceDiagram
  actor U as Usuario demo
  participant W as FastAPI
  participant B as BackgroundTasks
  participant G as LangGraph
  participant C as Anthropic
  participant D as Postgres
  U->>W: POST ficción
  W->>B: Programar
  W-->>U: Redirección inmediata
  B->>G: Procesar caso
  G->>C: Extraer tras controles PII
  C-->>G: Hechos
  G->>C: Tipificar v3
  C-->>G: Propuesta
  G->>D: Persistir y auditar
  B->>D: Commit por caso
  U->>W: Consultar bandeja
  W->>D: Leer casos
  D-->>W: Propuestas y estados
  W-->>U: HTML
  U->>W: Revisión humana
  W->>D: Revisión y evento; commit
```

## 4. Modelo de datos implementado

![Modelo de datos implementado](karin-4.svg)

**Uso:** GitHub · datos y auditoría. Expone las cinco tablas, campos de fundamento y limitaciones reales. Orientado a revisión de esquema y migraciones.

**Sustituye la vista antigua de:** Diez tablas, reidentificación, corpus e identidad institucional.

```mermaid
erDiagram
  DENUNCIA ||--o{ PRECLASIFICACION : tiene
  DENUNCIA ||--o{ EVENTO_AUDITORIA : registra
  PRECLASIFICACION ||--o{ REVISION_HUMANA : recibe
  DENUNCIA {
    string id PK
    string id_externo_dt UK
    string texto_seudonimizado
    string estado
  }
  PRECLASIFICACION {
    string id PK
    string denuncia_id FK
    string version_pipeline
    json justificacion_y_citas
  }
  REVISION_HUMANA {
    string id PK
    string preclasificacion_id FK
    int nivel
    string motivo_descarte
    string cita_respaldo
    boolean excepcion_rd10
    int version
  }
  EVENTO_AUDITORIA {
    int id PK
    string denuncia_id FK
    json detalle
    string hash_actual
  }
  USO_DIARIO {
    date fecha PK
    int llamadas
    float usd
  }
```

## 5. Despliegue de la edición pública

![Despliegue de la edición pública](karin-5.svg)

**Uso:** GitHub; anexo técnico comercial. Muestra la infraestructura que sí se usa y evita presentar GKE o ClaveÚnica como capacidades existentes.

**Sustituye la vista antigua de:** Heroku staging, GKE UAT/prod y servicios de GCP.

```mermaid
flowchart TD
  GH[GitHub público] --> B[Build Docker]
  B --> R[Release Alembic]
  R --> W[Un dyno Basic: Uvicorn + FastAPI]
  U[Navegador] --> H[Router HTTPS] --> W
  CV[Config Vars] --> W
  W --> DB[(Postgres Essential-0)]
  W --> C[API Anthropic]
```

## 6. Flujo real de verificación y publicación

![Flujo real de verificación y publicación](karin-6.svg)

**Uso:** GitHub · reproducibilidad. Distingue los pasos manuales comprobados de una automatización CI/CD que no está versionada.

**Sustituye la vista antigua de:** GitHub Actions, mypy, Trivy, eval-real y gates automatizados.

```mermaid
flowchart LR
  A[Rama de trabajo] --> B[pytest y Ruff]
  B --> C[Revisar diff y secretos]
  C --> D[Publicar GitHub]
  D --> E[git push heroku HEAD:main]
  E --> F[Build Docker]
  F --> G[Release Alembic]
  G --> H[Verificar HTTPS, login y persistencia]
```

## 7. Evidencia disponible y siguiente etapa

![Evidencia disponible y siguiente etapa](karin-7.svg)

**Uso:** GitHub; anexo de la ficha ampliada. Útil para explicar madurez y próximos pasos. No es una promesa de calendario ni una certificación institucional.

**Sustituye la vista antigua de:** Gantt de trece semanas y fecha comprometida de piloto sombra.

```mermaid
flowchart TD
  A[Implementación publicada] --> E[Evidencia técnica acotada]
  B[261 pruebas; once casos] --> E
  C[Comparación real v2 y v3] --> E
  E -. pendientes .-> P[Video; incógnito; límite consola; aceptación]
  E -. propuesta futura .-> F[Piloto institucional con autorizaciones]
```

## 8. Revisión humana: responsabilidades y estados

![Revisión humana: responsabilidades y estados](karin-8.svg)

**Uso:** Ficha de negocio y README. Hace visible el control humano y la doble revisión. Es el complemento de negocio más útil al diagrama de contexto.

**Sustituye la vista antigua de:** Orquestación CHIEF/R1–R7 y ciclos multiagente.

```mermaid
flowchart TD
  A[Pendiente de revisión humana] --> B{Descarte o excepción RD-10}
  B -->|no| C[Primera firma según permisos]
  B -->|sí| D[Inspector con fundamento obligatorio]
  C --> E[Revisado; segunda firma disponible]
  D --> F[Pendiente de supervisor]
  E -. opcional .-> G[Supervisor distinto; control de versión]
  F --> G
  G --> H[Validación humana completada]
```
