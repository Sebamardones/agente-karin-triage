# KARIN triage · Ficha de negocio

Grupo 7 · UAI · Noviembre de 2026. Prototipo público con datos sintéticos.

**Desarrollo ampliado:** [caso de negocio en HTML](FICHA_NEGOCIO_AMPLIADA.html),
con el formato visual de la bitácora del equipo, escenarios económicos y plan
de validación. [Abrir versión pública](https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/estaticos/ficha-negocio.html).
La ficha PDF de una página se conserva como resumen de la entrega.

## Cliente y problema

Dirección del Trabajo de Chile: inspectores y supervisores de recepción de
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

## Costos estimados de operación

| Concepto | Costo mensual |
|---|---:|
| Heroku Basic | USD 7 |
| Postgres Essential-0 | USD 5 |
| Inferencia de demostración, según uso | Presupuesto USD 3 |
| **Demo, total referencial** | **USD 15** |

En la corrida histórica v2 se estimaron USD 0,1889 / 6 casos con LLM =
**USD 0,0315 por caso** (incluidos reintentos de esa muestra). No es costo
garantizado ni tarifa del proveedor conciliada. La nueva corrida v3 estima
USD 0,1600 / 9 casos = **USD 0,0178 por caso**. **USD 0,10 por caso es un
presupuesto conservador**, aproximadamente tres veces ese valor, para variación
de longitud y reintentos; no es el costo observado. A 1.000 casos/mes: presupuesto
de inferencia USD 100, más USD 12 de infraestructura, antes de soporte y desarrollo.
Las tarifas codificadas aún deben conciliarse con factura vigente.

## Adopción, protección y validación

La demo permite registrar ingresos de caso sintéticos (con los mismos campos que
procesa el sistema) y tandas para revisión sin borrar historial. La edición institucional requiere validación jurídica, autorización
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
