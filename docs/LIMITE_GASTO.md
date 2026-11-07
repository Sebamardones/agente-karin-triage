# Límite de gasto del proveedor

Estado: **PENDIENTE** hasta que exista `docs/evidencia/limite-gasto-consola.png`.
Al completar el procedimiento, cambiar este estado a «Configurado» con la fecha.

## Tres capas de control

| Capa | Dónde vive | Qué corta | Estado |
|---|---|---|---|
| Límite mensual del workspace | Consola de Anthropic, workspace `karin-triage-demo` | Toda llamada con la clave del workspace, sin importar quién la haga | PENDIENTE |
| Tope diario en código | `KARIN_TOPE_LLAMADAS_DIA=200` y `KARIN_TOPE_USD_DIA=3.0` (Config Vars) | Llamadas de esta aplicación; marca `PRESUPUESTO_AGOTADO` | Activo |
| Manejo del rechazo del proveedor | `agent/nodos.py` · `ejecutar_llm` | Si el proveedor rechaza la llamada, el caso queda en cola humana con RD-16 | Activo |

Los topes en código **no reemplazan** el límite de la consola: cuentan con
tarifas `PENDIENTE_VERIFICAR`, viven en un solo proceso y no ven llamadas hechas
con la misma clave fuera de la aplicación (por ejemplo, el runner de evals).
El límite de la consola es la capa que exige la pauta del curso.

Monto propuesto: **USD 20 mensuales, con alerta en USD 10.** Una corrida del
golden set cuesta entre USD 0,16 y 0,28 y un caso nuevo cerca de USD 0,018
(`docs/MEJORA_PROMPTS.md`). El tope diario de USD 3 evita que un abuso consuma
el mes completo en un día; el límite mensual es el techo absoluto.

### Valores para operar (1.581 casos al mes, 10 analistas y 5 supervisores)

Los valores anteriores son los de la demo. Con 1.581 casos al mes (unos 75 por
día hábil) los topes de la demo frenarían la operación: en un día normal se
hacen unas 150 llamadas, hasta 226 con reintentos, y el presupuesto diario es
USD 7,53. Detalle del cálculo en [FICHA_NEGOCIO.md](FICHA_NEGOCIO.md).

| Capa | Demo | Operación |
|---|---:|---:|
| `KARIN_TOPE_LLAMADAS_DIA` | 200 | 400 |
| `KARIN_TOPE_USD_DIA` | 3,0 | 8,0 |
| Límite mensual en la consola | USD 20 | USD 170 |

## Por qué un workspace propio y una clave nueva

La consola no permite fijar un límite propio al workspace por defecto: este
sigue siempre el límite de la organización. Un workspace dedicado aísla el gasto
de la demo, empieza el mes en cero y obliga a emitir una clave nueva, lo que
además rota la clave usada hasta ahora.

## Procedimiento (quien administra la cuenta de Anthropic)

1. En la configuración de facturación de la organización, fijar un límite
   mensual de organización y una notificación por debajo de ese monto.
2. Crear el workspace `karin-triage-demo`.
3. En los límites de gasto del workspace, fijar **USD 20** y alerta en **USD 10**.
4. Crear una API key **dentro** de ese workspace. No copiarla en archivos,
   chats ni capturas.
5. Reemplazar el secreto en Heroku (reinicia el dyno):
   `heroku config:set ANTHROPIC_API_KEY=<clave nueva> -a karin-triage-grupo7`
6. Probar: crear un relato ficticio en `/demo/nuevo` y confirmar que vuelve con
   propuesta y citas.
7. Recién después, revocar la clave antigua. Actualizar también el entorno
   local del runner de evals.
8. Guardar una captura de los límites del workspace (monto y alerta visibles,
   sin la clave) en `docs/evidencia/limite-gasto-consola.png`.
9. Cambiar «PENDIENTE» por «Configurado (fecha)» en este archivo, en el README,
   en `docs/FICHA_NEGOCIO.md` (y regenerar el PDF) y en
   `docs/CORRECCIONES_EVALUACION.md`.

## Qué ve el usuario si se alcanza el límite

El proveedor rechaza la llamada. Desde el commit que agrega este documento, el
caso **no se pierde**: se guarda sin propuesta, con la marca «Modelo no
disponible · revisión manual», regla RD-16 y prioridad 0. Antes de ese cambio,
el error hacía fallar el grafo y el caso no se guardaba. Lo prueba
`backend/tests/test_grafo.py::test_07b_error_del_proveedor_va_a_cola_manual`.
