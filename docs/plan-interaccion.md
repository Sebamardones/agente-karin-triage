# Plan de interacción · puesto de trabajo del funcionario

Fecha: 2026-11-08. Complementa `docs/plan-diseno.md`, que fijó la identidad
visual DT, y se mantiene dentro de ella. Este plan cambia **cómo se trabaja**:
la cola de casos, la forma de presentar la propuesta del modelo, la manera de
decidir y el paso de un caso entre bandejas.

## Restricciones que no cambian

- Ningún caso se resuelve solo: toda acción la ejecuta una persona.
- El descarte exige motivo, comentario y cita literal, y lo valida un
  supervisor distinto (RD-11, ADR-019). La excepción a RD-10 sigue igual.
- Sin cambios de esquema, migraciones ni dependencias. Todo sale de datos que
  ya existen: `fecha_ingesta`, `urgencia_resguardo`, `prioridad`,
  `justificacion_y_citas`, `reglas_aplicadas`, `marcas_pipeline`,
  `RevisionHumana` (`nivel`, `rol`, `coincide_con_agente`).
- Servidor con Jinja2 y htmx (ADR-016): sin frameworks de frontend.
- Nada simulado. Cada indicador se calcula desde la base; si un dato no
  existe, no se muestra.

## 1. Bandejas por estado, según el rol

Se reemplaza la tabla única por pestañas con contador. El estado se deriva de
`estado_revision`, que ya existe.

| Pestaña | Inspector ve | Supervisor ve |
|---|---|---|
| Por revisar | Casos sin revisión | Casos sin revisión que puede firmar |
| Esperando supervisor | Descartes y excepciones RD-10 que firmó, en espera | **Por validar**: lo que le toca firmar (pestaña principal) |
| Revisados | Con revisión de nivel 1, segunda revisión opcional | Igual |
| Cerrados | Validación humana completada | Igual |

Las tandas anteriores siguen fuera de la vista principal, en el historial.

## 2. Cola de tarjetas en vez de tabla

- **Carriles:** «Urgentes» (urgencia de resguardo) arriba y «Por revisar»
  abajo, cada uno ordenado por prioridad y antigüedad.
- **Cada tarjeta muestra:** identificador, antigüedad («hace 2 h», desde
  `fecha_ingesta`), chip de decisión propuesta, chip de urgencia, conducta y
  una línea de contexto: la primera cita del relato, recortada.
- Los casos sin IA (RD-01 a RD-06, proveedor caído) muestran el chip «Sin IA»
  con la regla que los detuvo. Así se ve de un vistazo qué casos costaron
  cero.
- En móvil la cola ocupa toda la pantalla y el caso abre como página.

## 3. Panel de decisión, sin salir de la cola

En escritorio, al elegir una tarjeta, el caso se carga a la derecha con htmx
(vista maestro-detalle). La URL cambia (`hx-push-url`), así que el enlace al
caso sigue funcionando.

**Cómo entrega el modelo su resultado:**
1. **Veredicto en una frase:** «El agente propone: procede investigación por
   acoso sexual», con chips de urgencia, confianza y «N citas verificadas».
2. **Relato con las citas resaltadas en su lugar.** Las citas del relato son
   literales (RD-15), así que se ubican con búsqueda exacta y se marcan con
   `<mark>` numerado. Las citas normativas van debajo, con su referencia.
3. **Recorrido del caso:** una línea de pasos (reglas previas →
   seudonimización → IA → validación de citas → reglas posteriores), armada
   con `reglas_aplicadas` y `marcas_pipeline`. Si una regla corrigió al modelo
   (por ejemplo RD-10), el paso lo dice en lenguaje claro.
4. **Justificación** del modelo, plegable y abierta por defecto.

**Cómo decide la persona.** Tres acciones, una sola primaria:

| Acción | Qué pasa |
|---|---|
| **Confirmar propuesta** | Un clic registra la revisión con la decisión del agente. Si el caso es un descarte, abre el paso del descarte |
| **Corregir** | Despliega las decisiones alternativas como botones grandes y un comentario. Si elige mediación en acoso sexual, aparece la advertencia RD-10 con su comentario obligatorio |
| **Descartar** | Abre un paso guiado: motivo (botones del catálogo), cita (**se selecciona con el mouse en el relato** y se copia sola al campo) y comentario. El botón final dice «Enviar a supervisor» |

El supervisor ve, en vez de la propuesta sola, **la comparación**: «El agente
propuso X · el inspector decidió Y», con el comentario y la cita del inspector.
Sus acciones son «Validar» (misma decisión) o «Decidir distinto».

## 4. Paso entre bandejas y retroalimentación

- Al registrar, la tarjeta sale de la cola con una animación corta y aparece
  un aviso: «Caso confirmado · pasó a Revisados» o «Enviado a supervisor
  para validación». Los contadores de las pestañas se actualizan.
- **El siguiente caso se abre solo**, sin volver a la lista.
- El supervisor ve el caso nuevo en «Por validar» en el siguiente refresco (5 s),
  con la animación de entrada que ya existe.

## 5. Relato nuevo: seguimiento hasta el resultado

Hoy, después de enviar, la persona vuelve a la bandeja a buscar su caso. La
propuesta: después de enviar, una página de seguimiento consulta cada 2 s si
el caso ya existe (por su `id_externo_dt`, guardado en la sesión) y **abre el
resultado solo** cuando está listo. Mientras espera muestra el estado real
(«En cola», «Analizando»), sin pasos inventados. Si falla, lo dice y ofrece
volver a la bandeja.

## 6. Extras para la demo (solo si sobra tiempo)

- Atajos de teclado en la cola: `j`/`k` para moverse, `c` para confirmar y `?`
  para ver la ayuda.
- Franja de métricas: casos revisados hoy, coincidencia agente–persona (desde
  `coincide_con_agente`) y casos que no llegaron a la IA.

## Animaciones nuevas (mismo criterio del catálogo A1–A5)

| # | Dónde | Función | Detalle | Movimiento reducido |
|---|---|---|---|---|
| A6 | Panel de caso al abrir desde la cola | Transición | Fundido de 150 ms; sin desplazamiento | Instantáneo |
| A7 | Tarjeta que sale de la cola al decidir | Confirmación | Se pliega en 250 ms con la curva de salida | Desaparece |
| A8 | Aviso «pasó a…» | Confirmación | Entra en 200 ms y queda 4 s, con `role="status"` | Sin movimiento |
| A9 | Cita resaltada al pasar el mouse por su número | Transición | Cambio de fondo en 150 ms | Instantáneo |

## Esfuerzo y orden

| Bloque | Esfuerzo | Prioridad |
|---|---|---|
| 1 + 2 · Bandejas por rol y cola de tarjetas | 3 h | Imprescindible |
| 3 · Panel maestro-detalle, veredicto, citas resaltadas, recorrido y acciones | 5 h | Imprescindible |
| 4 · Paso entre bandejas, aviso y siguiente caso | 2 h | Imprescindible |
| 5 · Seguimiento del relato nuevo | 1,5 h | Imprescindible (es la escena del video) |
| 6 · Atajos y métricas | 2 h | Opcional |
| Pruebas, accesibilidad y capturas | 2 h | Imprescindible |

Total imprescindible: unas 13,5 h. La entrega es el viernes 13 a las 23:59 y
el video se graba sobre esta versión: lo imprescindible debería quedar
desplegado el martes 10, para tener el miércoles y el jueves para el video y la
documentación.

## Riesgos

- Es un cambio grande de plantillas. Las 267 pruebas actuales protegen las
  reglas de revisión; las pruebas de textos de la bandeja se reescriben.
- La selección de texto para la cita necesita JavaScript propio. Si falla, el
  campo de cita sigue siendo editable a mano.
