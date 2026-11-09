# ADR-021 · Puesto de trabajo, ingreso de caso y perfil «inspector»

Fecha: 2026-11-08. Estado: aceptada e implementada (releases Heroku v14–v21).

## Contexto

La bandeja era una tabla única de ocho columnas: mezclaba tandas antiguas con
casos vigentes, mostraba códigos internos y obligaba a abrir cada caso en otra
página para decidir. La pauta del curso pide un flujo «fácil de usar por
alguien externo». Además, el perfil de primera revisión se llamaba «analista»,
cuando en la Dirección del Trabajo esa función la ejerce un inspector.

## Decisión

1. **Puesto de trabajo maestro-detalle**, con la cola a la izquierda y el caso
   a la derecha, sobre la misma pila de Jinja2 y htmx (ADR-016). No se agrega un
   framework de frontend ni dependencias. El comportamiento vive en
   `api/estaticos/interaccion.js` y la presentación de solo lectura en
   `api/presentacion.py`.
2. **Bandejas derivadas del estado humano**, sin columnas nuevas: Por revisar,
   Esperando supervisor (para el supervisor, «Por validar»), Revisados,
   Cerrados y Tandas anteriores. Salen de `estado_revision` y de las revisiones
   existentes.
3. **La propuesta se presenta verificada al mostrarla**: las citas del relato
   se buscan tal cual en el texto seudonimizado (la misma tolerancia de
   espacios que RD-15) y se marcan en su lugar. Una cita que no aparece no se
   marca ni se cuenta. `reglas_aplicadas` no se usa como prueba de
   verificación, porque RD-15 registra el fallo, no el éxito.
4. **Las reglas de revisión humana no cambian**: firma por niveles, descarte
   con motivo, comentario y cita, supervisor distinto y excepción RD-10. La
   interfaz solo las hace visibles: el descarte guiado termina en «Enviar a
   supervisor».
5. **«Ingreso de caso»** reemplaza a «Probar la IA con un relato sintético»
   (`/ingresos/nuevo`; `/demo/nuevo` redirige). Pide los campos que procesa el
   pipeline: tipo de ingreso, fecha, empleador, sector y relato. Así RD-02,
   RD-03 y RD-05 se activan desde el formulario. Folios `ING-<12 hex>`.
6. **No se piden datos de identidad de quien denuncia** (nombre, RUT,
   contacto): el sistema no guarda identidades y la edición no acepta datos
   reales (regla 2 de `CLAUDE.md`). Se mantiene una declaración obligatoria de
   que el ingreso no contiene datos personales reales, validada en el servidor.
7. **El perfil «analista» pasa a «inspector»** en la interfaz, el rol interno,
   el usuario (`inspector_demo`), las pruebas y la documentación. La contraseña
   sigue en `KARIN_DEMO_PASSWORD_ANALISTA` para no cambiar la configuración de
   Heroku. Las revisiones antiguas conservan `analista_demo` como funcionario y
   muestran su rol como «inspector». Los prompts versionados v1 y v2 no se
   modifican, porque la medición de mejora depende de ellos.
8. **Recursos estáticos versionados por contenido** (`?v=<sha256>` en CSS y
   JS), porque `StaticFiles` no envía `Cache-Control`.

## Consecuencias

- La suite pasó de 261 a 283 pruebas. Se reescribieron las pruebas que leían
  estados en la tabla única; las reglas de firma, descarte y RD-10 se
  mantienen sin cambios.
- El usuario de acceso cambió: hay que informar `inspector_demo` en la
  plataforma del curso.
- La interfaz se aparta de la norma gráfica de redes sociales de la DT en las
  formas redondeadas y en los iconos; queda documentado en `plan-diseno.md`,
  sección 8.
- Detalle de diseño en `docs/plan-diseno.md` y `docs/plan-interaccion.md`;
  capturas en `docs/capturas/`.
