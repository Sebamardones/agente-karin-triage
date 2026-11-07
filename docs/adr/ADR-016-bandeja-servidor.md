# ADR-016 · Bandeja renderizada en el servidor con Jinja2 y HTMX

- **Estado**: Aceptado solo para la edición de entrega del 13-11-2026
- **Fecha**: 2026-11-07
- **Desvía**: Q18 del registro de decisiones (*«Bandeja React + Vite + TS»*)

## Contexto

Q18 fijó la bandeja web en React + Vite + TypeScript, con un `api_client`
generado a partir del OpenAPI de FastAPI. Es la decisión correcta para el
piloto: una bandeja con filtros avanzados, estados de carga y uso diario
sostenido merece un frontend de verdad.

Pero esa decisión se tomó con un horizonte de 13 semanas. Quedan seis días para
la entrega del Proyecto Final, y el camino React cuesta, como mínimo: un build
multi-etapa en el Dockerfile, la generación y el versionado del cliente
TypeScript, el manejo de estados de carga y error en el cliente, y la
configuración de CORS o de servido de estáticos. Nada de eso aporta puntos en
la pauta, que evalúa que la URL pública abra y complete el flujo principal.

## Decisión

Para esta edición la bandeja se renderiza en el servidor con Jinja2, y las
interacciones puntuales (confirmar, corregir, paginar) usan HTMX sobre
fragmentos HTML. Un solo proceso, una sola imagen, cero Node en el build.

La API JSON de FastAPI **se conserva** y sigue generando su OpenAPI: los
endpoints son los mismos que consumiría el frontend React. Eso mantiene abierta
la vuelta a Q18 sin rehacer el backend.

## Alternativas descartadas

- **React + Vite + TS, como manda Q18.** Descartada por cronograma, no por
  mérito técnico. Es a lo que se vuelve en el piloto.
- **Bandeja JSON sin interfaz, solo con la documentación de FastAPI.** Habría
  sido más rápida todavía, pero la pauta exige que el flujo principal se
  complete desde un navegador. La documentación interactiva de OpenAPI no es
  una bandeja de revisión.

## Consecuencias

- Se liberan cerca de dos días de cronograma, que van a los prompts, al golden
  set y al video: los tres criterios con brecha real.
- La interfaz es más pobre. Para seis casos sintéticos y dos roles de
  demostración, alcanza.
- Hay una deuda declarada: volver a Q18 en el piloto. Queda en la hoja de ruta
  del `README.md`.
- La regla de stack del proyecto exige un ADR para desviarse, y este es ese
  ADR. No se introduce ninguna plataforma ni servicio nuevo: Jinja2 es una
  librería OSS mantenida y HTMX se sirve como estático desde la propia imagen.
