# ADR-003 · Llamadas al LLM con el SDK oficial `anthropic`

- **Estado**: Aceptado (ratifica el ADR-003 que quedó `Propuesto` en la Parte A)
- **Fecha**: 2026-11-07
- **Decide**: equipo técnico
- **Verificación**: documentación vigente del SDK de Anthropic, consultada el
  2026-11-07

## Contexto

La Parte A de la arquitectura dejó el ADR-003 como *«Propuesto: ratificar en el
ciclo 001»* y usó en sus ejemplos de código cuatro elementos de API que no
estaban confirmados: `messages.parse`, `output_config` con `effort`, el caché
del prefijo con TTL de una hora, y un *fallback* de servidor tras un encabezado
beta. La retroalimentación del profesor (sección 4.6) pidió explícitamente
verificarlos antes de usarlos y marcar `PENDIENTE_VERIFICAR` lo que no se
encuentre.

## Resultado de la verificación

| Elemento usado en la Parte A | Veredicto | Detalle |
|---|---|---|
| `client.messages.parse(..., output_format=ModeloPydantic)` → `response.parsed_output` | **Confirmado** | Es la vía recomendada para salida estructurada validada. Se mantiene tal cual |
| `output_config={"effort": "low" \| "medium"}` | **Confirmado** | Disponible sin encabezado beta. Va dentro de `output_config`, no en el nivel superior. Niveles: `low`, `medium`, `high`, `xhigh`, `max`; el valor por omisión es `high` |
| `cache_control={"type": "ephemeral", "ttl": "1h"}` en un bloque de `system` | **Confirmado** | Máximo 4 puntos de corte por solicitud. El prefijo mínimo cacheable depende del modelo, así que un prefijo corto no cachea y no avisa |
| `stop_reason == "refusal"` y `stop_details` | **Confirmado** | `stop_details` se llena **solo** cuando `stop_reason` es `refusal`; en cualquier otro caso es `null`. Hay que comprobarlo antes de leerlo. RD-16 queda bien fundada |
| **Modelo `claude-sonnet-5-5`** | **CORREGIDO — no existe** | El identificador vigente es **`claude-sonnet-5`**. El de la familia superior es **`claude-opus-5`**, no `claude-opus-5-5` |
| «Sin `thinking: disabled`, que devuelve 400 en Sonnet 5.5» | **CORREGIDO — es falso** | En `claude-sonnet-5`, `thinking: {"type": "disabled"}` se acepta. Igual **no se usa**: el control de costo se hace con `effort`, que es lo que la Parte A quería lograr |
| «Sin `tool_choice` forzado, que devuelve 400 en Sonnet 5.5» | **CORREGIDO — es falso para este modelo** | La restricción aplica a otros modelos de la familia, no a `claude-sonnet-5`. Es irrelevante para el diseño: el LLM no tiene herramientas (regla 6 de `CLAUDE.md`) |
| `fallbacks` de servidor con beta `server-side-fallback-2026-07-01` | **`PENDIENTE_VERIFICAR` para `claude-sonnet-5`** | El mecanismo existe y la forma documentada es `betas=["server-side-fallback-2026-07-01"]` con `fallbacks="default"`, pero está documentado para los modelos de la familia superior. No se encontró confirmación para `claude-sonnet-5` |
| `inference_geo="us"` | No se usa en esta edición | Solo tenía sentido para declarar jurisdicción en la EIPD, y esta edición no procesa datos reales (D-KARIN-08) |

## Decisión

1. Las llamadas al LLM usan el SDK oficial `anthropic` dentro de los nodos del
   grafo, con `messages.parse` y `output_format` apuntando a los modelos
   Pydantic de `models/salidas_llm.py`.
2. El modelo es **`claude-sonnet-5`** en los dos nodos LLM. `claude-opus-5`
   queda detrás de una variable de entorno apagada, como ya definía Q24.
3. El prefijo normativo va como bloque de `system` con
   `cache_control` de TTL de 1 hora, y debe ser **estable byte a byte**: sin
   fechas, sin identificadores, sin contadores. Se verifica leyendo
   `usage.cache_read_input_tokens`.
4. El costo se controla con `effort`: `low` en `extraer_hechos` y `medium` en
   `tipificar_y_proponer`.
5. **No se usa el *fallback* de servidor en esta edición.** Un encabezado beta
   que podría devolver 400 en el modelo elegido es un riesgo de despliegue
   innecesario a seis días de la entrega, y RD-16 ya cubre el caso: ante
   `refusal` o error tras reintentos, el caso va a revisión humana marcado como
   `LLM_REFUSAL`, sin propuesta. Queda en la hoja de ruta.

## Consecuencias

- Se elimina un error que habría hecho fallar **todas** las llamadas en
  producción con un 404 de modelo inexistente. Es el hallazgo más valioso de
  esta verificación.
- Se pierde la degradación automática ante *refusal*. Es aceptable: en este
  dominio un *refusal* no debe resolverse cambiando de modelo a espaldas del
  funcionario, sino escalando a una persona.
- Las dos afirmaciones corregidas sobre errores 400 estaban escritas con
  seguridad y eran falsas. Queda como recordatorio de la regla 10 de
  `CLAUDE.md`: lo que no se verificó se marca, no se afirma.
