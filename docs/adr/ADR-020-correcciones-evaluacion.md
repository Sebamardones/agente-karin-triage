# ADR-020 · Demo renovable, revisión fundada y medición por fuente

Fecha: 2026-11-07. Alcance: edición académica con datos sintéticos.

## Problemas comprobados

Los casos agotaban sus dos revisiones; cargar el set existente no ejecutaba IA.
Una revisión humana podía descartar sin motivo o contradecir RD-10 sin advertirlo.
Las citas normativas se validaban contra el relato; el runner las aceptaba sin
comprobarlas. Una amenaza de pérdida de turnos elevaba urgencia indebidamente.

## Decisiones

- Formulario de ficción con confirmación explícita y límite de longitud; solo
  inspector. Tandas con IDs nuevos, sin eliminar casos ni historial.
- Descarte humano con catálogo, comentario y cita literal, rechazando fundamentos
  por falta de prueba. Los campos quedan en revisión humana mediante migración
  aditiva 0002; los eventos solo contienen motivo y bandera, sin comentario libre.
- RD-10 humana: advertencia y comentario; primera excepción por inspector y
  segunda revisión por otro supervisor. No se convierte en decisión automática
  ni se afirma que una excepción humana cambia el texto de la norma.
- Las citas se validan según su fuente; v3 produce solo citas de denuncia y
  fundamenta referencias legales en la justificación.
- RD-12 mantiene asimetría: nunca baja una urgencia activa. Para elevar una que
  está en false, una amenaza exclusivamente laboral sin indicios físicos no
  basta. La heurística es provisional y necesita validación del dueño del criterio.
- Catálogos legibles, estados explícitos y conteos persistidos de casos separados
  de los contadores de tarea en memoria. No se usa «Cerrado»: nadie cierra casos.
- Nueva medición de once casos y evidencia versionada, incluyendo la iteración
  insuficiente. No inventar medición de JSON cuando solo se observan objetos SDK.

## Consecuencias y límites

Migrar antes de arrancar. Revisiones históricas no se reescriben ni se les
inventa fundamento; la interfaz las identifica y ofrece una tanda nueva.
Se mantiene un dyno/un worker y tareas no durables. Los nuevos envíos consumen
IA y están sujetos a topes existentes. La declaración de ficción no garantiza
que un usuario no pegue información real; la interfaz lo prohíbe y el pipeline
aplica seudonimización y corte residual. El video y la evidencia de límite de
consola requieren actuación del equipo/operador.
