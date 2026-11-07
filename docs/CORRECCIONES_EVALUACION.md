# Trazabilidad de correcciones de EVALUACION_KARIN_TRIAGE

Fuente: archivo del operador EVALUACION_KARIN_TRIAGE.md, revisión 2026-11-07.
No se publica el archivo original para evitar confundir la evaluación previa
con el estado corregido. Objetivo: cerrar cada observación con evidencia.

| Observación | Corrección y evidencia |
|---|---|
| Evaluador no puede ejecutar IA | Formulario `/demo/nuevo`, confirmación de ficción y procesamiento real en segundo plano |
| Casos agotan revisiones | Nueva tanda con IDs diferentes; no borra historial ni modifica revisiones ajenas |
| RD-10 humana | Advertencia normativa, comentario obligatorio y supervisor distinto para validar una excepción |
| Descarte humano sin motivo | Motivo de catálogo, comentario y cita literal obligatorios; no se permite falta de prueba |
| Urgencia sobrestimada | v3 separa urgencia y gravedad; RD-12 distingue amenaza laboral sin riesgo físico y mantiene asimetría |
| Enums crudos | Filtro de etiquetas en bandeja, ficha e historial |
| Pipeline vacío | «Alertas» y «Sin marcas» |
| Contador confuso | Total guardado en base y contadores ocultos si no hay actividad de carga |
| Estados ambiguos | Pendiente, revisión con segunda firma disponible, pendiente supervisor, validación humana completada |
| Tilde | «Datos sintéticos» |
| Nuevo prompt | `prompts/tipificar_v3.md`; v1/v2 intactos |
| Runner | Denominadores reales; errores incluidos; citas por fuente; contador sexual independiente de ID |
| Tercer positivo y casos independientes | G-09, G-10 y G-11: once casos, tres positivos de urgencia |
| Medición real | Comparación v2/v3 y cuatro JSON en `evals/evidencia/`, incluidas corridas insuficientes |
| README | Ruta nodos, referencias públicas, reglas reservadas, carga completa y límite no confirmado corregidos |
| No hay RAG | Se documenta `<dictamenes>` vacío |
| Ficha PDF | Una página, cifras oficiales, Compra Ágil condicionada, precio propuesto, costo observado frente a presupuesto |
| Guion | Actualizado a v2/v3 y a formulario real; no sustituye video grabado |

## Resultados locales

Suite completa intermedia: 253 aprobadas, Ruff sin hallazgos. Incluye migración
SQLite upgrade/downgrade, controles de revisión humana, fuentes de citas,
denominadores de métricas, creación de ficción y tandas sin borrar historial.
La evidencia final del despliegue se agrega a VERIFICACION_PUBLICA.md.

Verificación final: commit 2ed92a2, release Heroku v10 succeeded. Migración
Postgres 0002 confirmada. Formulario real con IA y respuesta de envío 0,86 s;
rechazo de descarte incompleto y revisión persistida entre sesiones comprobados.
La tanda final quedó con once casos, cero revisiones y pipeline v3/reglas2.
Después de preparar esa tanda se hicieron solo consultas de lectura.

Medición final bajo el mismo pipeline reglas2: decisiones 9/9 en ambas,
citas v2 25/29 frente a v3 22/22, salida válida sin reintento 5/9 frente a 9/9,
urgencia 9/9 y positivos 3/3 en ambas. Costo estimado 0,2142 a 0,16 USD (25,3%
menos). No se interpreta esto como garantía estadística ni medición de JSON crudo.

## Pendientes que no se declaran cumplidos

- Límite de USD 20 en la consola de Anthropic: pendiente de configuración y
  evidencia del operador. No se cambió la clave y no se afirma que esté aplicado.
  El procedimiento (workspace dedicado, clave nueva, captura) está en
  [LIMITE_GASTO.md](LIMITE_GASTO.md). Ya resuelto en código: un rechazo del
  proveedor deja el caso en cola manual con RD-16 en vez de perderlo.
- Video real de máximo tres minutos: pendiente de grabación por el equipo.
  No hay acceso al navegador/escritorio automatizado para grabar esta sesión.
- Inspección visual manual en incógnito: pendiente del equipo; se realizan
  comprobaciones HTTPS con sesiones independientes, sin llamarlas inspección visual.

Los cambios de software y documentos no garantizan una nota ni sustituyen la
validación jurídica y la aceptación de fases por el responsable humano.
