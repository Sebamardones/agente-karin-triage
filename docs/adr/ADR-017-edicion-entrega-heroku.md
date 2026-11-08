# ADR-017 · Edición de entrega: un solo servicio en Heroku, sin ClaveÚnica

- **Estado**: Aceptado solo para la edición de entrega del 13-11-2026
- **Fecha**: 2026-11-07
- **Afecta**: Q3, Q17, Q19/Q30, Q21, Q23, Q29

## Contexto

La arquitectura apuntaba a GKE Autopilot en `southamerica-west1` como
producción, con Cloud SQL, Cloud KMS, Cloud Armor, Langfuse *self-hosted*,
autenticación con ClaveÚnica (OIDC), autorización con tabla propia más RLS por
inspección, ingesta horaria desde Mi DT y un entorno UAT intermedio. Heroku
figuraba como *staging* con datos sintéticos (Q3, Q17).

La retroalimentación identificó esto como el problema crítico de la entrega: con
ClaveÚnica y una tabla de funcionarios autorizados, **el profesor no podría
entrar a evaluar**. Y la pauta exige que la URL pública abra y complete el flujo
principal en una ventana de incógnito. Un despliegue que nadie externo puede
abrir vale cero en «Software funcional» y en «Despliegue», es decir 45 de los
100 puntos.

## Decisión

La edición de entrega se publica como **un solo servicio en Heroku**, con la
misma imagen Docker que luego corre en cualquier otra parte:

- **Plataforma**: Heroku con *stack* de contenedor (`heroku.yml`). Heroku ya
  estaba aprobado en Q3, así que no se introduce una plataforma nueva.
- **Datos**: Heroku Postgres. No se usa SQLite en el entorno publicado: el
  sistema de archivos de un dyno es efímero y los datos se perderían en cada
  reinicio. SQLite se mantiene en dev y tests, como fija Q4.
- **Acceso**: login de demostración con dos usuarios, `inspector_demo` y
  `supervisor_demo`. Las contraseñas son secretos de la plataforma
  (`heroku config:set`) y se entregan al profesor por la plataforma del curso,
  nunca por el repositorio.
- **Autorización**: los dos roles se distinguen en la aplicación. **No** hay RLS
  por inspección: el piloto es de una sola inspección y la RLS no se puede
  demostrar con dos usuarios de prueba.
- **Observabilidad**: logs estructurados a la salida estándar, que es lo que
  Heroku recoge. Nada de Langfuse.
- **Ingesta**: carga manual de las denuncias sintéticas del golden set desde la
  propia bandeja. Nada de CronJob horario.
- **Presupuesto**: límite de USD 20 en la consola de Anthropic, más un tope
  diario de llamadas y de gasto en el código (`KARIN_TOPE_LLAMADAS_DIA`,
  `KARIN_TOPE_USD_DIA`). Al tocar el tope, la marca `PRESUPUESTO_AGOTADO` manda
  el caso a cola manual en vez de seguir llamando.

## Lo que queda explícitamente fuera

GKE, UAT, Cloud KMS, Cloud Armor, Langfuse *self-hosted*, ClaveÚnica, RLS por
inspección, EIPD, autorización del encargado de datos, set histórico real, modo
sombra e ingesta horaria. Todo documentado como hoja de ruta en el `README.md`.

## Consecuencias

- El profesor puede entrar con dos credenciales y completar el flujo. Eso
  convierte «Software funcional» de insuficiente en evaluable.
- Desaparecen de la ruta crítica todas las autorizaciones externas: registro de
  ClaveÚnica, autorización de datos, EIPD. Era el mayor riesgo de factibilidad.
- Se pierde la demostración de RLS, que era una de las piezas técnicas más
  sólidas del diseño. Se compensa documentándola en el README y dejando la
  política SQL escrita en la hoja de ruta.
- Hay una divergencia real entre el entorno publicado y el de destino. Se
  acota manteniendo una sola imagen Docker y toda la configuración por variables
  de entorno, igual que preveía la mitigación de RG-10.
