# ADR-019 · El descarte lo abre el inspector y lo valida un supervisor

- **Estado**: Aceptado
- **Fecha**: 2026-11-07

## Problema

La segunda revisión de un descarte exige un supervisor distinto de quien hizo la
primera. La edición publicada tiene un solo supervisor (`supervisor_demo`). Si
ese supervisor firmaba la primera revisión de un caso con propuesta
`DESCARTADO` (o marcaba él mismo `DESCARTADO`), nadie podía hacer la segunda: el
inspector recibía 403 por rol y el supervisor 403 por ser la misma persona. El
caso quedaba trabado (ocurrió con SINT-0007 en producción).

Además, la interfaz no mostraba esos rechazos: htmx no intercambia respuestas
4xx, así que el botón parecía no hacer nada.

## Decisión

- La primera revisión de un descarte la hace siempre el inspector: el supervisor
  no puede abrir un caso con propuesta `DESCARTADO` ni registrar `DESCARTADO` en
  una primera revisión.
- El nivel 2 es siempre una validación: lo firma un supervisor distinto de quien
  firmó el nivel 1, sea cual sea la decisión. Antes esa exigencia solo se
  activaba si el descarte venía de la propuesta o del nivel 1, así que un
  descarte firmado recién en el nivel 2 pasaba sin supervisor (SINT-0001).
- La ficha del caso oculta el formulario y explica el motivo cuando el usuario
  conectado no puede revisar; el supervisor no ve la opción `DESCARTADO` en una
  primera revisión.
- Los rechazos del servidor se muestran bajo el formulario y, tras una revisión
  exitosa, la ficha se recarga para reflejar el historial.

## Consecuencias

El flujo de doble revisión de un descarte se puede completar con las dos cuentas
de demostración. Los casos ya trabados antes de este cambio requieren corregir
los datos por el operador.
