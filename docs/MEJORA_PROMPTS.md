# Actualización: comparación v2 contra v3 corregida

Fecha: 2026-11-07. Esta sección sustituye las conclusiones de preparación de
publicación anteriores; la comparación histórica v1/v2 se conserva más abajo.
Once casos sintéticos (nueve decisiones y dos estados auxiliares), tres positivos
de urgencia. Mismo runner corregido, mismo golden set y mismas reglas2 para ambas
versiones de la comparación final. Los prompts v1 y v2 permanecen intactos.

| Métrica final | v2 | v3 |
|---|---:|---:|
| Decisión final correcta | 9/9 | 9/9 |
| Estado auxiliar | 2/2 | 2/2 |
| Citas verificadas contra su fuente | 25/29 (86%) | 22/22 (100%) |
| Salida estructurada y citas válidas sin reintento | 5/9 | 9/9 |
| Urgencia correcta (positivos y negativos) | 9/9 | 9/9 |
| Positivos de urgencia detectados | 3/3 | 3/3 |
| Falsos positivos de urgencia | 0 | 0 |
| Acoso sexual enviado a mediación por el modelo | 0 | 0 |
| Falsos descartes finales | 0 | 0 |
| Errores | 0 | 0 |
| Llamadas al cliente LLM | 22 | 18 |
| Costo estimado USD | 0,2142 | 0,1600 |

Mejora observada: cuatro llamadas menos y USD 0,0542 menos (25,3%), con cuatro
casos adicionales válidos sin reintento y validación literal 100%. El costo v3
por caso que usa IA fue aproximadamente USD 0,0178 (0,16/9). Las tarifas del
código siguen pendientes de conciliación con la factura del proveedor.

**No se afirma una medición de JSON crudo.** El SDK devuelve objetos parseados;
`json_valido_al_primer_intento=null` significa no observable. La métrica correcta
es salida de esquema más citas sin reintento, sobre los nueve casos con LLM.
Los casos sin modelo no se cuentan como éxitos y los errores no desaparecen
del denominador. El contador de mediación sexual usa tipos esperados/propuestos,
sin depender de G-02. Las citas normativas se contrastan con el prefijo real.

## Cambios y atribución

v3 separa urgencia de gravedad moral y efectos laborales, distingue la represalia
sindical sin acoso y limita las citas a fragmentos de denuncia. La referencia
legal sigue en la justificación. El validador admite citas normativas exactas
para otras versiones, pero v3 evita producirlas de memoria.

La primera pareja de corridas dio urgencia 8/9 en ambas y resultados insuficientes
de citas (v2 24/29, borrador v3 18/27). No se publicó ese borrador. Se afinó v3
y se calibró RD-12 para no elevar por amenazas exclusivamente laborales sin
señal física. RD-12 conserva toda urgencia ya marcada y protege amenazas físicas.
La mejora de urgencia 8/9 a 9/9 es del pipeline común, **no se atribuye solo al
prompt**. La diferencia final de citas y reintentos sí compara v2/v3 bajo las
mismas reglas. La versión del pipeline cambia a `reglas2`.

## Evidencia y reproducción

Los cuatro JSON de esta revisión, sin relatos ni secretos, están versionados en
[`evals/evidencia/`](../evals/evidencia/). Los dos finales son:

- `tipificar_v2-2026-11-07T215855+0000.json`
- `tipificar_v3-2026-11-07T215840+0000.json`

Incluyen detalle por caso y hashes SHA-256 del prompt y golden set. Para repetir,
desde backend, con clave en el entorno privado y presupuesto autorizado:

```powershell
uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v2.md
uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v3.md
```

Las dos corridas iniciales también se conservan. Su borrador v3 ya no coincide
con el prompt final; su hash identifica esa diferencia. Los resultados son
observaciones de una corrida por versión por iteración, no garantía estadística
ni generalización. G-09/G-10/G-11 amplían el set con situaciones independientes;
v3 no incluye ejemplos resueltos que copien esos relatos.

---

## Registro histórico v1/v2 (antes de estas correcciones)

# Mejora medida de prompts - KARIN triage

Fecha de revisión: 2026-11-07. Comparación de `tipificar_v1.md` y
`tipificar_v2.md` sobre los mismos ocho casos sintéticos. No se ejecutaron
nuevas llamadas pagadas durante esta revisión.

## Evidencia y reproducción

Archivos locales originales en `evals/salidas/`:

- `tipificar_v1-2026-11-07T155044+0000.json`
- `tipificar_v2-2026-11-07T155305+0000.json`

Comandos del runner, desde `backend/` (requieren una clave nueva configurada
fuera del repositorio y consumen presupuesto):

```powershell
uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v1.md
uv run --python 3.12 python ../evals/runner.py --prompt tipificar_v2.md
```

La corrida v1 de las 15:46 UTC tuvo seis errores y no se usa como línea base.
Su resumen `8/8` de JSON no significa ocho respuestas válidas: el runner
cuenta como éxito las filas sin indicador de reintento, incluso ante error.

## Qué cambió

v1 establece rol, delimitación de datos, criterios y esquema, pero deja los
ejemplos pendientes. v2 añade un procedimiento ordenado, dos ejemplos positivos
y uno negativo, instrucciones de copia literal y antipatrones. Los ejemplos
se parecen a casos del golden set: es evaluación de regresión conocida, no
evidencia de generalización sobre denuncias nuevas. La afirmación del prompt
de que todos los antipatrones fueron observados en v1 no queda demostrada por
estas corridas: ambas tienen cero errores de decisión finales.

## Resultados originales del runner

| Métrica | v1 | v2 |
|---|---:|---:|
| Decisión final correcta (casos con decisión esperada) | 6/6 | 6/6 |
| Estado auxiliar correcto | 2/2 | 2/2 |
| Citas reportadas como literales | 23/23 (100%) | 20/20 (100%) |
| JSON válido al primer intento, indicador del runner | 2/8 | 3/8 |
| Urgencia: solo casos esperados positivos | 2/2 | 2/2 |
| Acoso sexual enviado a mediación por el modelo, indicador del runner | 0 | 0 |
| Falsos descartes finales | 0 | 0 |
| Errores de ejecución | 0 | 0 |
| Llamadas LLM | 18 | 17 |
| Costo estimado por el código, USD | 0,1942 | 0,1889 |

Se mantiene el resultado de decisión y se ahorra una llamada: USD 0,0053,
aproximadamente 2,73% por corrida. Una única corrida por versión, con ocho casos,
no permite atribuir causalidad ni afirmar una mejora estadísticamente robusta.
Los costos usan tarifas del código marcadas `PENDIENTE_VERIFICAR`; no son
importes conciliados con la factura del proveedor.

## Límites de medición y metas pendientes

- G-04 y G-05 no llaman al modelo. Al excluirlos, el indicador de ausencia
  de reintento en casos con LLM es **0/6 en v1 y 1/6 en v2**. Ni siquiera este
  indicador mide exclusivamente sintaxis JSON: también refleja validación de
  esquema y citas. No se cumple ni se demuestra la meta de JSON inicial >=7/8.
- La urgencia sobre los seis casos con valor esperado es **5/6 en v1 y 4/6
  en v2**. Ambas versiones detectan los dos positivos; v1 tiene un falso
  positivo (G-06), y v2 tiene dos (G-01 y G-06). El golden set contiene dos
  positivos, por lo que no demuestra la meta de tres positivos del prompt maestro.
- `literal()` devuelve verdadero automáticamente para las citas normativas;
  la tabla no constituye una comprobación independiente de esas citas.
  RD-15 valida la salida durante el flujo, pero el runner debe separar fuentes.
- El contador de acoso sexual a mediación depende de G-02 y además busca
  `ACOSO_SEXUAL` en las reglas o el ID; puede omitir una propuesta incorrecta.
  Se requiere revisar `decision_del_modelo` por caso y mejorar el contador.
- Las decisiones medidas son posteriores a reglas deterministas: el 6/6 no
  demuestra por sí solo exactitud del modelo sin las reglas.

## Hallazgo G-01 y seguimiento

En v2, G-01 esperaba `urgencia_resguardo=false` y obtuvo `true`; en v1 obtuvo
`false`. La regla RD-12 solo puede elevar urgencia, nunca reducirla. Se conserva
esa protección: no se cambia una regla jurídica para mejorar artificialmente
una métrica. G-06 también esperaba `false` y obtuvo `true` en ambas versiones.

Próxima iteración propuesta: calibrar en una versión nueva qué evidencia textual
sostiene riesgo inmediato; agregar casos independientes y un tercer positivo
de urgencia; corregir denominadores y contadores del runner con pruebas de
regresión; repetir varias corridas con la clave rotada y registrar modelo,
configuración y uso real. Mantener v1 intacta. No declarar F5 aprobada ni el
proyecto listo para publicación con estos umbrales pendientes.
