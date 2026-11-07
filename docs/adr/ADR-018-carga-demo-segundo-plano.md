# ADR-018 - Carga de demostración en segundo plano

Fecha: 2026-11-07. Estado: implementado para la demostración de un dyno.

## Problema

La primera prueba pública devolvió HTTP 503 al solicitar los ocho casos: las
llamadas reales a Claude superan el tiempo de respuesta del router Heroku.
El procesamiento seguía en el servidor, pero el navegador veía un error.

## Decisión

Usar BackgroundTasks de FastAPI, con una sesión SQLAlchemy propia por tarea y
retorno inmediato a la bandeja. Mostrar contadores y enlace para actualizar.
Un lock por proceso impide programar dos cargas simultáneas. Los casos ya
persistidos se omiten por su identificador sintético. No se añade un servicio.

## Consecuencias

Los casos y revisiones quedan en Postgres; los contadores y tareas no son
durables. Un reinicio puede interrumpir la carga: volver a solicitarla continúa
con los casos no guardados. El lock se limita al proceso; usar un dyno y un
worker. Escalar exige una cola y coordinación persistentes. El tope diario de
gasto se mantiene. No se procesa información real ni se automatizan decisiones.

## Verificación

La suite existente pasó (230 pruebas). Se agregó una prueba que retiene la
tarea, comprueba respuesta y progreso sin ejecutarla, impide duplicados y
ejecuta luego la carga: las 18 pruebas de API pasan. Ruff no tiene hallazgos.
La aceptación de fases sigue correspondiendo al operador.
