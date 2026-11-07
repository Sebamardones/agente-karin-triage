# KARIN triage · Ficha de negocio

Grupo 7 · UAI · Noviembre de 2026. Prototipo público con datos sintéticos.

## Cliente y problema

Dirección del Trabajo de Chile: analistas y supervisores de recepción de
denuncias. El balance oficial registra **44.212 denuncias entre agosto de 2024
y junio de 2025**, unas 4.019 por mes. **17.980 (40%)** se preclasificaron como
no Ley Karin y se cerraron. La carga de clasificación y la necesidad de revisar
criterios consistentes justifican probar apoyo al funcionario; el tiempo humano
ahorrado debe medirse en un piloto, no se declara demostrado.

## Propuesta de valor e IA

Extraer hechos de relatos en lenguaje natural y proponer tipificación con citas
literales y reglas trazables. Seudonimizar antes de llamar al modelo; cortar el
flujo si queda PII residual; validar esquemas y citas contra su fuente. Reglas
deterministas RD-01 a RD-06 y RD-10 a RD-16 (RD-07 a RD-09 reservadas).
El agente propone; una persona decide. Descartar requiere motivo, comentario,
cita y segunda revisión. Las excepciones humanas RD-10 quedan advertidas y
requieren validación de otro supervisor. No hay RAG: `<dictamenes>` va vacío.

## Precio y modelo de ingresos propuestos

**Servicio anual por inspección: CLP 3.600.000 + IVA** (equivalente a CLP 300.000
mensuales), para un piloto de hasta 1.000 casos al mes. Incluye operación,
soporte básico y seguimiento de calidad. Volumen adicional: cotización separada
y costo de inferencia según consumo. Es una **hipótesis comercial del proyecto**,
no una tarifa contratada ni validada con la DT. Desarrollo institucional,
integraciones y asesoría jurídica se cotizan aparte.

Vía de entrada propuesta: **Compra Ágil**, si el total de la contratación queda
dentro de **100 UTM** y se cumplen las condiciones del procedimiento. Solicita
al menos tres cotizaciones y promueve participación de empresas de menor tamaño;
no garantiza adjudicación. Verificar UTM, impuestos y elegibilidad al cotizar.

## Consumo mensual estimado de operación

Escenario de operación: **10 analistas, 5 supervisores y 1.581 casos ingresados
al mes**, unos 75 por día hábil (supuesto: 21 días hábiles al mes).

| Concepto | Observado | Presupuesto |
|---|---:|---:|
| Inferencia por caso | USD 0,0178 | USD 0,10 |
| Inferencia, 1.581 casos | USD 28,11 | USD 158,10 |
| Heroku Basic + Postgres Essential-0 | USD 12 | USD 12 |
| **Total mensual** | **USD 40,11** | **USD 170,10** |
| Costo total por caso | USD 0,025 | USD 0,108 |

El costo observado sale de la corrida v3: USD 0,16 para nueve casos con IA
(dos llamadas por caso). Se supone que todos los casos usan IA; los que las
reglas deterministas resuelven antes (sector público, registro incompleto)
cuestan cero, así que el cálculo es conservador. **USD 0,10 por caso es el
presupuesto de planificación**, unas cinco veces lo observado, para cubrir
relatos más largos y reintentos. Las tarifas del código siguen pendientes de
conciliar con la factura del proveedor.

**Carga por persona.** Cada analista revisa unos 158 casos al mes (7,5 por día
hábil). La segunda firma de los descartes recae en los supervisores: si se
mantiene la proporción del balance oficial (40,7% preclasificado como no Ley
Karin), son unos 643 descartes al mes, 129 por supervisor (6 por día hábil).
El número de usuarios no cambia el costo de IA, que depende solo de los casos.

**Capacidad.** Un dyno Basic atiende a 15 usuarios con esta carga. Postgres
Essential-0 tiene 1 GB: con un supuesto conservador de 50 KB por caso,
incluida la auditoría, se usan unos 77 MB al mes y alcanza para cerca de un
año; después corresponde Essential-1 (USD 9, 10 GB).

**Topes de gasto para operar.** Los topes de la demo (200 llamadas y USD 3 al
día) frenarían la operación: en un día normal se hacen unas 150 llamadas, hasta
226 con reintentos, y el presupuesto diario es USD 7,53. Para operar se fijan
**400 llamadas y USD 8 al día** en código, y **USD 170 al mes** en la consola
de Anthropic.

**Relación con el precio.** El plan propuesto cubre hasta 1.000 casos al mes:
este escenario lo supera en 581 casos, que se cotizan como volumen adicional.

## Adopción, protección y validación

La demo permite crear relatos ficticios nuevos y tandas para revisión sin borrar
historial. La edición institucional requiere validación jurídica, autorización
de datos y evaluación de privacidad antes de admitir información real. Se mide
calidad, tiempo de revisión y falsos descartes antes de ampliar el servicio.
La seudonimización heurística y las pruebas sintéticas no garantizan anonimato
ni cumplimiento legal integral. Topes diarios de código; límite de proyecto en
consola pendiente de evidencia del operador.

## Fuentes

- [Balance oficial Mintrab, 1 de agosto de 2025](https://www.mintrab.gob.cl/ministerio-del-trabajo-y-ministerio-de-la-mujer-presentan-balance-de-la-ley-karin-a-un-ano-de-su-implementacion/).
- [Informe DT, agosto de 2024 a junio de 2025](https://www.dt.gob.cl/portal/1626/articles-128897_archivo_01.pdf).
- [Compra Ágil, ChileCompra](https://www.chilecompra.cl/compraagil/).
- [Precios Heroku](https://www.heroku.com/pricing/).

Aplicación: https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/
