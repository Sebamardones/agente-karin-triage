# KARIN triage · Ficha de negocio

Grupo 7 · UAI · Noviembre de 2026. Prototipo público con datos sintéticos.

**Desarrollo ampliado:** [caso de negocio en HTML](FICHA_NEGOCIO_AMPLIADA.html),
con el formato visual de la bitácora del equipo, escenarios económicos y plan
de validación. [Abrir versión pública](https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/estaticos/ficha-negocio.html).
La ficha PDF de una página se conserva como resumen de la entrega.

## Cliente y problema

Dirección del Trabajo de Chile: inspectores y supervisores de recepción de
denuncias. El informe estadístico semestral de la DT con corte al 30 de junio
de 2026 registra **92.643 ingresos asociados a denuncias entre el 1 de agosto
de 2024 y el 30 de junio de 2026**: 33.156 por oficinas, 44.938 por Mi DT y
14.549 derivados por empleadores. El primer semestre de 2026 sumó 25.830, unos
**4.305 por mes**. **32.565 (35%)** se clasificaron para continuar como Ley
Karin, **48.505 (52%)** se derivaron o cerraron y 11.573 (12%) seguían
pendientes. La carga de clasificación y la necesidad de revisar
criterios consistentes justifican probar apoyo al funcionario; el tiempo humano
ahorrado debe medirse en un piloto, no se declara demostrado.

**Usuarios proyectados: 400.** Son 200 inspectores dedicados exclusivamente a
la recepción de casos Ley Karin y 200 funcionarios con dedicación no exclusiva,
entre ellos los supervisores. Si toda la recepción recayera en los 200
dedicados, cada uno atendería unos 22 ingresos al mes.

## Propuesta de valor e IA

Extraer hechos de relatos en lenguaje natural y proponer tipificación con citas
literales y reglas trazables. Seudonimizar antes de llamar al modelo; cortar el
flujo si queda PII residual; validar esquemas y citas contra su fuente. Reglas
deterministas RD-01 a RD-06 y RD-10 a RD-16 (RD-07 a RD-09 reservadas).
El agente propone; una persona decide. Descartar requiere motivo, comentario,
cita y segunda revisión. Las excepciones humanas RD-10 quedan advertidas y
requieren validación de otro supervisor. No hay RAG: `<dictamenes>` va vacío.

**Por qué importa el tiempo.** La pre-clasificación corre contra plazos
legales: **2 días hábiles** para pedir medidas de resguardo (art. 211-B bis del
Código del Trabajo) y **30 días** para concluir la investigación (art. 211-C).
Si la Inspección no se pronuncia en 30 días sobre un informe interno, se tienen
por válidas las conclusiones del empleador. La propuesta llega ordenada por
urgencia, con las citas que la fundan, para que el funcionario decida antes
de que venza el plazo.

## Precio y modelo de ingresos propuestos

**Unidad del piloto: un equipo de recepción de 10 analistas y 5 supervisores**
(15 usuarios), con un volumen de referencia de **1.581 casos al mes**, unos 75
por día hábil (supuesto: 21 días hábiles). Es cerca del 37 % del ritmo nacional
de 4.305 ingresos mensuales del primer semestre de 2026. El volumen es un
supuesto del equipo: qué oficina o dirección regional concentra ese volumen
queda `PENDIENTE_VERIFICAR` con la DT.

**Servicio anual por unidad de recepción: CLP 5.400.000 + IVA** (CLP 450.000
mensuales netos), con **hasta 1.600 casos al mes**. Equivale a unos CLP 285 por
caso. Incluye operación, diez horas de soporte al mes y seguimiento de calidad.
Sobre 1.600 casos, cada caso adicional cuesta CLP 150. Es una **hipótesis
comercial del proyecto**, no una tarifa contratada ni validada con la DT.
Desarrollo institucional, integraciones y asesoría jurídica se cotizan aparte.

**Margen estimado del piloto** a 1.581 casos al mes (CLP 1.000 por USD como
supuesto):

| Concepto | Presupuesto conservador | Tasa observada v3 |
|---|---:|---:|
| Ingreso mensual (neto de IVA) | CLP 450.000 | CLP 450.000 |
| Inferencia, 1.581 casos | CLP 158.100 (USD 0,10/caso) | CLP 28.110 (USD 0,0178/caso) |
| Infraestructura (Heroku Basic + Postgres) | CLP 12.000 | CLP 12.000 |
| Soporte, 10 h × CLP 15.000 | CLP 150.000 | CLP 150.000 |
| Seguimiento de calidad | CLP 40.000 | CLP 40.000 |
| **Margen bruto mensual** | **CLP 89.900 (20 %)** | **CLP 219.890 (49 %)** |

La inferencia es el único costo variable: con menos casos el margen sube, y en
el tope de 1.600 casos el margen conservador sigue en CLP 88.000 (20 %). No
incluye desarrollo, adquisición del cliente ni impuestos a la renta; el margen
comercial no está demostrado.

**Valor para la DT.** Con un costo de oportunidad de CLP 9.000 por hora de
funcionario (supuesto del equipo), el precio equivale a unos **2 minutos por
caso**, incluida la adopción (15 usuarios × 2 h, amortizada en un año). Si el
sistema libera más de 2 minutos netos por caso, el piloto se paga en capacidad.
Ese ahorro es la hipótesis que mide el piloto; no está demostrado.

Vía de entrada propuesta: **Compra Ágil**, si el total de la contratación, con
IVA (unos CLP 6.426.000), queda dentro de **100 UTM** y se cumplen las
condiciones del procedimiento. El valor de la UTM al cotizar queda
`PENDIENTE_VERIFICAR`. Solicita al menos tres cotizaciones y promueve la
participación de empresas de menor tamaño; no garantiza adjudicación.

## Costos estimados de operación

### Demostración pública

| Concepto | Costo mensual |
|---|---:|
| Heroku Basic | USD 7 |
| Postgres Essential-0 | USD 5 |
| Inferencia de demostración, según uso | Presupuesto USD 3 |
| **Demo, total referencial** | **USD 15** |

### Piloto: 1.581 casos al mes, 10 analistas y 5 supervisores

| Concepto | Observado | Presupuesto |
|---|---:|---:|
| Inferencia por caso | USD 0,0178 | USD 0,10 |
| Inferencia, 1.581 casos | USD 28,11 | USD 158,10 |
| Heroku Basic + Postgres Essential-0 | USD 12 | USD 12 |
| **Total mensual de plataforma** | **USD 40,11** | **USD 170,10** |

El costo observado sale de la corrida v3: USD 0,16 para nueve casos con IA (dos
llamadas por caso). En la corrida histórica v2 se estimaron USD 0,0315 por caso,
con los reintentos de esa muestra. Se supone que todos los casos usan IA; los
que las reglas deterministas resuelven antes (sector público, registro
incompleto) cuestan cero, así que el cálculo es conservador. **USD 0,10 por caso
es el presupuesto de planificación**, unas cinco veces lo observado
(0,10 / 0,0178 ≈ 5,6), para cubrir relatos más largos y reintentos. Las tarifas
del código siguen pendientes de conciliar con la factura del proveedor.

**Carga por persona.** Cada analista revisa unos 158 casos al mes (7,5 por día
hábil). La segunda firma de los descartes recae en los supervisores: si se
mantiene la proporción del balance oficial (40,7 % preclasificado como no Ley
Karin), son unos 643 descartes al mes, 129 por supervisor (6 por día hábil).

**Capacidad.** Un dyno Basic atiende a 15 usuarios con esta carga. Postgres
Essential-0 tiene 1 GB: con un supuesto conservador de 50 KB por caso, incluida
la auditoría, se usan unos 77 MB al mes y alcanza para cerca de un año; después
corresponde Essential-1 (USD 9, 10 GB, `PENDIENTE_VERIFICAR` al cotizar).

**Topes de gasto para operar.** Los topes de la demo (200 llamadas y USD 3 al
día) frenarían el piloto: en un día normal se hacen unas 150 llamadas, hasta 226
con reintentos, y el presupuesto diario es USD 7,53. Para operar se fijan
**400 llamadas y USD 8 al día** en código y **USD 170 al mes** en la consola de
Anthropic ([`LIMITE_GASTO.md`](LIMITE_GASTO.md)).

### Despliegue nacional proyectado (400 usuarios, 4.305 casos/mes)

Supuesto de cálculo: CLP 1.000 por USD.

| Concepto | Costo mensual |
|---|---:|
| 2 dynos web + 1 worker Standard-2X (USD 50 c/u, PENDIENTE_VERIFICAR) | USD 150 |
| Postgres Standard-0 (PENDIENTE_VERIFICAR) | USD 50 |
| Inferencia presupuestada, 4.305 × USD 0,10 | USD 431 |
| Soporte para 400 usuarios, 40 h × CLP 15.000 | CLP 600.000 |
| Seguimiento de calidad | CLP 160.000 |
| **Total operativo** | **≈ CLP 1.391.000** |

Equivale a unos **CLP 16,7 millones al año**, CLP 3.478 por usuario y CLP 323
por caso al mes. A la tasa observada en v3, la inferencia bajaría a unos
USD 77. Con holgura para 5.000 casos/mes, el total sube a unos CLP 1.460.000.
La adopción de 400 usuarios (2 h por persona a CLP 9.000) suma CLP 7.200.000
una vez. No incluye desarrollo institucional, integración con Mi DT ni
ClaveÚnica. Ese monto supera el límite de Compra Ágil y requeriría otro
procedimiento de compra; la tarifa por unidad de recepción cubre solo el piloto.

## Adopción, protección y validación

La demo permite registrar ingresos de caso sintéticos (con los mismos campos que
procesa el sistema) y tandas para revisión sin borrar historial. La edición institucional requiere validación jurídica, autorización
de datos y evaluación de privacidad antes de admitir información real. Se mide
calidad, tiempo de revisión y falsos descartes antes de ampliar el servicio.
La seudonimización heurística y las pruebas sintéticas no garantizan anonimato
ni cumplimiento legal integral. Topes diarios de código y límite mensual de
USD 20 en la consola de Anthropic, configurado el 9 de noviembre de 2026.

## Fuentes

- [Dirección del Trabajo, *Informe estadístico semestral sobre denuncias en
  materias de la Ley N.° 21.643 con corte al 30 de junio de 2026*, agosto de
  2026](https://www.dt.gob.cl/portal/1626/articles-129626_archivo_01.pdf).
- [Informe DT, agosto de 2024 a junio de 2025](https://www.dt.gob.cl/portal/1626/articles-128897_archivo_01.pdf), antecedente anterior cuyas cifras ajustó el informe de 2026.
- [Compra Ágil, ChileCompra](https://www.chilecompra.cl/compraagil/).
- [Precios Heroku](https://www.heroku.com/pricing/).

Aplicación: https://karin-triage-grupo7-c7c6a3fb2988.herokuapp.com/
