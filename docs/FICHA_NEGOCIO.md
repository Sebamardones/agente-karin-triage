# agente-karin-triage · Ficha de negocio

Pre-clasificación asistida de denuncias de Ley Karin para la Dirección del
Trabajo · Grupo 7 · noviembre de 2026

---

## Cliente

**Dirección del Trabajo de Chile (DT)**, y en particular las Inspecciones
Provinciales y Comunales que reciben denuncias por acoso laboral, acoso sexual
y violencia en el trabajo bajo la Ley 21.643.

Usuarios directos: funcionarios y funcionarias con rol de analista y de
supervisor en la etapa de recepción e ingreso de denuncias.

## Problema

La propia Dirección del Trabajo informó **44.212 denuncias entre el 1 de agosto
de 2024 y el 30 de junio de 2025** — unas **4.019 al mes** — en el informe que
está obligada a emitir por el artículo 26 del DS N° 21 de 2024.[^1]

De esas 44.212, el informe detalla que **18.367 (42%) fueron pre-clasificadas
como Ley Karin y 17.980 (40%) fueron pre-clasificadas como *no* Ley Karin y
cerradas**, quedando un 18% pendiente de clasificación.[^1]

Ese dato define el negocio: **la etapa de pre-clasificación no hay que
inventarla ni convencer a nadie de que debería existir.** Existe, es
obligatoria, procesa unas 44 mil denuncias al año y descarta el 40% de ellas.
Hoy se hace a mano.

Y corre contra plazos legales que no admiten holgura:

- **2 días hábiles** para que la Inspección solicite al empleador medidas de
  resguardo (art. 211-B bis del Código del Trabajo).
- **30 días** para concluir la investigación (art. 211-C).
- **30 días** para pronunciarse sobre un informe de investigación interna; si
  la Inspección no lo hace, **se tienen por válidas las conclusiones del
  empleador** (art. 211-C).

El tercer plazo es el más revelador: el silencio de la institución no es
neutro, favorece al empleador investigado. Un atraso administrativo tiene
consecuencias jurídicas sobre la persona que denunció.

## Solución

Un pre-clasificador que, por cada denuncia ingresada, entrega al funcionario una
propuesta fundada en menos de un minuto:

1. **Reglas duras deterministas** en código (RD-01 a RD-16) resuelven primero
   lo que no admite interpretación: sector público se deriva, informe interno
   queda fuera de alcance, registro incompleto pide antecedentes, denuncia
   anterior al 1 de agosto de 2024 se rige por el régimen previo.
2. **Seudonimización antes de cualquier llamada al modelo**, con corte del flujo
   si queda algún dato personal residual.
3. **Dos funciones de IA generativa acotadas**: una extrae los hechos del
   relato; la otra propone tipificación, urgencia de resguardo y decisión,
   **fundándola en citas literales** de la denuncia y de la norma, que se
   verifican automáticamente carácter por carácter.
4. **Reglas duras posteriores** corrigen al modelo: la más importante impide
   que un caso de acoso sexual sea derivado a mediación, porque el art. 211-D
   inciso final exceptúa expresamente esa conducta de la mediación previa del
   art. 486 inciso sexto.

### El principio de producto

**Ningún caso se resuelve solo.** El sistema no decide, no notifica y no cierra:
propone, y un funcionario confirma o corrige. Todo descarte exige una segunda
revisión de un supervisor distinto. Es a la vez una decisión ética, la condición
para que la institución lo adopte, y la respuesta a la objeción sindical
previsible.

## Rol de la IA generativa

Dos llamadas a `claude-sonnet-5` por caso, con salida estructurada validada
contra un esquema Pydantic. El modelo **no tiene herramientas**: no escribe en
la base de datos, no re-identifica personas y no determina competencia
institucional. Su única salida es un objeto validado con citas verificables.

Lo que la IA aporta y una regla no podría: leer un relato en lenguaje natural,
muchas veces escrito por la persona afectada en primera persona y sin
estructura, y decidir si lo descrito encaja en una de las tres conductas del
artículo 2 inciso segundo. El resto del sistema es determinista a propósito.

## Modelo de ingresos · B2G

| Etapa | Vía de contratación | Monto referencial |
|---|---|---|
| **Piloto en una inspección** | Compra Ágil en Mercado Público, hasta 100 UTM | El costo anual estimado de operación cabe bajo ese tope |
| **Extensión regional** | Licitación pública tipo CO, entre 100 y 1.000 UTM | Según alcance |
| **Despliegue nacional** | Licitación pública, sobre 1.000 UTM, con publicación previa de la intención de contratar | Según alcance |

Ingreso recurrente por **servicio anual de operación y soporte**, con el costo
de inferencia traspasado por volumen de casos procesados.

El servicio es, además, sostenible para el Estado porque el costo marginal por
caso es ínfimo frente al costo de la hora de funcionario que libera: a 4.000
casos al mes, la inferencia cuesta del orden de **USD 400 al mes**.

> Los umbrales en UTM y la modalidad aplicable están tomados de documentación de
> ChileCompra y manuales de adquisiciones 2025-2026, y quedan
> `PENDIENTE_VERIFICAR` contra el texto del DS N° 661 antes de cualquier
> presentación formal. La investigación completa, con sus fuentes, está en
> `docs/investigacion/KT-001-ficha-b2g.md`.

## Costo mensual de operar la aplicación

**De esta entrega (demostración pública con denuncias sintéticas):**

| Componente | Costo |
|---|---|
| Dyno Basic en Heroku, siempre activo | USD 7 |
| Heroku Postgres Essential-0 | USD 5 |
| Inferencia (`claude-sonnet-5`, uso de demostración) | ≈ USD 3 |
| **Total** | **≈ USD 15 / mes** |

Con un límite de gasto de **USD 20** configurado en la consola de Anthropic, y
un tope diario de llamadas y de dólares en el propio código: al alcanzarlo, el
caso se marca `PRESUPUESTO_AGOTADO` y pasa a cola manual en vez de seguir
llamando al modelo.

**A escala institucional**, el costo de inferencia es de **USD 0,10 por caso**,
desglosado en `docs/ARQUITECTURA.md`: prefijo normativo cacheado, dos llamadas
y un 20% de reintentos. Por volumen:

| Casos al mes | Inferencia |
|---|---|
| 2.000 | USD 200 |
| **4.019 (volumen real informado)** | **≈ USD 400** |
| 6.000 | USD 600 |

## Por qué ahora

- La Ley 21.643 está vigente desde el 1 de agosto de 2024 y su volumen de
  denuncias ya se estabilizó en torno a las 4.000 mensuales.
- El **87,5%** de los casos son de acoso laboral y el **66,4%** de las
  denuncias las presentan mujeres,[^1] lo que da contenido concreto al principio
  de perspectiva de género del artículo 211-B.
- La **Ley 21.719** de protección de datos personales rige desde el 1 de
  diciembre de 2026. Un sistema que seudonimiza antes de cualquier llamada
  externa y corta el flujo ante datos residuales nace alineado con ella, en vez
  de tener que adaptarse después.

## Riesgos principales

| Riesgo | Mitigación |
|---|---|
| Un falso descarte deja a una persona sin protección | Prohibición absoluta de descartar por falta de prueba, doble revisión obligatoria de todo descarte y meta de cero falsos descartes |
| Fuga de datos personales hacia el modelo | Seudonimización previa, detector de PII residual que corta el flujo, y tests de fuga sobre todo el golden set |
| Inyección de instrucciones en el relato | El relato va delimitado y tratado como dato, el modelo no tiene herramientas, la salida es estructurada y hay reglas posteriores. Está probado con un caso del golden set |
| Ciclo de compra pública lento | El piloto entra por Compra Ágil, que no requiere bases formales |
| Resistencia interna a la automatización | «Ningún caso se resuelve solo»: el sistema no reemplaza al funcionario, le quita de encima el 40% que hoy descarta a mano |

---

[^1]: Dirección del Trabajo, *Informe de denuncias por «Ley 21.643: Prevención y
Protección contra el Acoso Laboral, Sexual y Violencia en el Trabajo»,
ingresadas entre 1° agosto 2024 y 30 de junio 2025*, julio de 2025.
<https://www.dt.gob.cl/portal/1626/articles-128897_archivo_01.pdf>
Cifra confirmada por la Superintendencia de Seguridad Social, el Ministerio del
Trabajo y Previsión Social y la Organización Internacional del Trabajo.
