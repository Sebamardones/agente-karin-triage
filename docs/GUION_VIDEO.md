# Guion del video · 3 minutos máximo

Estructura que pide la pauta: **problema → demo en vivo → cómo lo construyeron.**

Presupuesto de tiempo, y es un presupuesto estricto:

| Bloque | Duración | Acumulado |
|---|---|---|
| 1 · El problema | 0:35 | 0:35 |
| 2 · La demo en vivo | 1:30 | 2:05 |
| 3 · Cómo lo construimos | 0:45 | 2:50 |
| Cierre | 0:10 | 3:00 |

**La demo se lleva la mitad del tiempo.** Es deliberado: la pauta exige ver IA
generativa activa en la URL publicada, y eso solo se demuestra mostrándola
funcionar.

### Antes de grabar

- Abre la URL en **incógnito** y entra una vez, para que el dyno esté despierto
  y la base tenga los casos cargados. Luego cierra y vuelve a abrir para grabar
  desde el login.
- Ten los casos **G-01** (acoso laboral), **G-02** (acoso sexual que pide
  mediación) y **G-04** (municipal) ya cargados en la bandeja.
- Ventana a 1920×1080 y zoom del navegador en 125%: el texto de las citas tiene
  que leerse en el video.
- Graba el audio aparte si puedes. Un video de 3 minutos con audio malo se
  escucha peor que uno con pantalla simple.

---

## Bloque 1 · El problema (0:35)

**En pantalla:** el informe de la Dirección del Trabajo abierto en la página de
las cifras, o una lámina con el número 44.212.

> La Dirección del Trabajo recibió 44.212 denuncias por acoso laboral, acoso
> sexual y violencia en el trabajo en los primeros once meses de la Ley Karin.
> Unas cuatro mil al mes.
>
> De esas, ella misma pre-clasificó 18.367 como Ley Karin y cerró 17.980 porque
> no lo eran. Esa etapa de pre-clasificación existe, es obligatoria por
> reglamento, y hoy se hace a mano.
>
> Y corre contra el reloj: dos días hábiles para pedir medidas de resguardo,
> treinta para cerrar la investigación. Y hay un detalle que cambia todo: si la
> Inspección no se pronuncia en treinta días sobre un informe interno, **valen
> las conclusiones del empleador**. El atraso no es neutro. Favorece a quien
> está siendo investigado.

**Por qué este bloque funciona:** no abre con la tecnología, abre con un número
oficial y con una consecuencia jurídica concreta. Y no exagera: la cifra es del
informe de la propia institución.

---

## Bloque 2 · La demo en vivo (1:30)

### 2.1 · Entrar (0:10)

**Acción:** login como `inspector_demo`.

> Entro como inspector de una Inspección. Son dos roles de demostración; los
> datos son todos sintéticos, no hay ninguna denuncia real acá.

### 2.2 · Un caso que procede (0:30)

**Acción:** abrir **G-01** y hacer scroll hasta las citas.

> Esta denuncia dice que una jefatura humilla a una trabajadora en la reunión
> de los lunes. El agente propone investigar, por acoso laboral.
>
> Pero lo que importa es esto: **no me dice solo qué decidió, me muestra con
> qué**. Esta cita es literal de la denuncia, y el sistema la verificó carácter
> por carácter contra el texto. Si no calzara, la propuesta se habría anulado.
>
> Y acá está la lista de reglas que se aplicaron. No es el modelo contándome lo
> que hizo: es el registro de qué código corrió.

### 2.3 · El caso difícil (0:35)

**Acción:** abrir **G-02**. Detenerse en la frase donde la persona pide
mediación.

> Este es el caso que de verdad pone a prueba el diseño. Hay acoso sexual, y la
> persona afectada pide expresamente que la citen a conversar y llegar a un
> acuerdo.
>
> Lo intuitivo sería derivar a mediación. Y está prohibido. El artículo 211-D
> inciso final excluye el acoso sexual de la mediación previa, porque mediar
> significaría sentar a la víctima a negociar con quien la acosó.
>
> El agente propone investigar y cita la norma. Y si el modelo se hubiera
> equivocado acá, hay una regla en código —RD-10— que corrige la decisión y
> deja constancia del error. **La parte que no se puede equivocar no se la
> preguntamos al modelo.**

### 2.4 · Corregir, y el caso que nunca llega al modelo (0:15)

**Acción:** corregir una propuesta y mostrar que queda registrada. Luego abrir
**G-04**.

> Yo decido. Confirmo o corrijo, y lo que corrijo queda registrado para medir
> cuánto coincide el agente conmigo.
>
> Y este último es un funcionario municipal. Una regla determinista lo deriva
> antes de llamar al modelo: **este caso costó cero**.

---

## Bloque 3 · Cómo lo construimos (0:45)

**En pantalla:** el diagrama del flujo del README, y después el repositorio con
la carpeta `prompts/` abierta.

> Tres capas, y el orden es el punto.
>
> Primero, **reglas duras en código**: dieciséis reglas con precedencia
> declarada y un test cada una. Lo que no admite interpretación no se le
> pregunta a un modelo de lenguaje.
>
> Segundo, **seudonimización antes de cualquier llamada**. Si queda un dato
> personal residual, el flujo se corta y el caso no sale del sistema.
>
> Tercero, **dos llamadas al modelo**, con salida estructurada validada y un
> prefijo normativo cacheado que lleva el texto literal de la ley.
>
> Los prompts están versionados en el repositorio y medidos: comparamos la
> versión 2 contra la versión 3 sobre once casos sintéticos, con cuatro
> métricas. Dos de ellas no se compensan con nada: **cero casos de acoso sexual
> a mediación y cero falsos descartes.** Si una versión del prompt falla ahí, no
> se publica, aunque el resto esté perfecto.
>
> Y una cosa que encontramos verificando: el documento original usaba un
> identificador de modelo **que no existe**. Lo habríamos descubierto en
> producción, con todas las llamadas fallando.

---

## Cierre (0:10)

> Ningún caso se resuelve solo. El agente propone, y una persona decide. Esa es
> la restricción de la que salen todas las demás decisiones de diseño.

---

## Qué NO decir

- No prometas que reemplaza al funcionario. El argumento es el contrario, y es
  además la respuesta a la objeción sindical.
- No digas «con un 95% de precisión» ni ninguna cifra que no esté medida en
  `docs/MEJORA_PROMPTS.md`.
- No muestres GKE, ClaveÚnica ni Langfuse como si estuvieran funcionando. Si
  los mencionas, es como hoja de ruta y se dice así.
- No leas la pantalla en voz alta. Di lo que la pantalla **no** muestra.
- No pidas disculpas por lo que falta. Tres minutos alcanzan para una cosa bien
  mostrada, no para un inventario.


## Actualización de la grabación tras la evaluación

Antes de grabar: usar la nueva tanda y dejar un caso sin revisar. No mostrar
Config Vars ni contraseñas. La grabación real sigue pendiente del equipo.

- 0:00-0:25: problema, cliente y precio propuesto de la ficha; no afirmar ahorro
  de tiempo medido ni una contratación ya validada.
- 0:25-1:30: entrar como inspector, abrir «Probar IA con un relato sintético
  nuevo», pegar ficción sin datos personales y enviar. Mostrar estado de carga,
  propuesta, citas y reglas. Explicar cualquier espera; no simular IA con
  respuestas escritas a mano.
- 1:30-2:10: mostrar descarte con motivo, comentario y cita; validarlo desde
  otra sesión como supervisor. Mostrar advertencia de excepción RD-10 si aplica.
- 2:10-2:45: abrir prompts v2/v3 y el informe de medición; citar resultados
  reales, los denominadores y los límites. No llamar JSON a una métrica de citas.
- 2:45-3:00: URL y repositorio; siguiente paso de validación institucional.

Una secuencia de capturas o el guion no sustituye el video de la demo en vivo.
