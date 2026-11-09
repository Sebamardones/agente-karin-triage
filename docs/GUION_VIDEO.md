# Guion del video · 3 minutos máximo

Estructura que pide la pauta: **problema → demo en vivo → cómo lo construyeron.**
Revisado el 9 de noviembre de 2026 contra la release v26 (landing `/entrar`,
puesto de trabajo con bandejas, «Ingreso de caso» y panel de decisión).

| Bloque | Duración | Acumulado |
|---|---|---|
| 1 · El problema | 0:30 | 0:30 |
| 2 · La demo en vivo | 1:35 | 2:05 |
| 3 · Cómo lo construimos | 0:40 | 2:45 |
| Cierre | 0:10 | 2:55 |

La narración tiene unas 420 palabras: a ritmo normal (unas 155 por minuto) son
2:40 de voz. Si el ensayo pasa de 2:55, recortar primero el bloque 3.

La meta es **2:55**: cinco segundos de margen bajo el máximo. La demo se lleva
más de la mitad del tiempo porque la pauta exige ver la IA generativa activa en
la URL publicada, y eso solo se demuestra mostrándola funcionar.

## Antes de grabar

1. **Límite de gasto configurado** (`docs/LIMITE_GASTO.md`). La tanda nueva y el
   caso en vivo gastan unos USD 0,25 en total.
2. Abrir la URL en **incógnito**, entrar como `inspector_demo` y usar
   «Más acciones → Crear tanda nueva». Esperar a que la bandeja muestre los
   once casos de la tanda (pulsar «Actualizar bandeja»). Así la cola parte
   limpia, con casos sin revisar.
3. Revisar en esa tanda el caso **SINT-0002** (acoso sexual con pedido de
   mediación) y anotar si aparece el aviso rojo «Una regla dura corrigió al
   modelo». El modelo no es determinista: el texto del bloque 2.3 tiene dos
   variantes según lo que muestre.
4. Copiar el relato del bloque 2.2 en un editor aparte, listo para pegar.
5. Cerrar sesión. La grabación parte en `/entrar`.
6. Ventana a 1440×900 o 1920×1080 y zoom del navegador en 125 %: las citas
   tienen que leerse en el video.
7. Grabar la voz aparte si es posible, en un lugar silencioso.

No mostrar Config Vars, contraseñas ni la consola de Anthropic con la clave
visible.

---

## Bloque 1 · El problema (0:30)

**En pantalla:** la landing `/entrar`, con las cifras animadas (92.643 · 4.305 ·
35 %). Bajar despacio hasta la fuente.

> La Dirección del Trabajo registró 92.643 ingresos por Ley Karin en sus
> primeros veintitrés meses: más de cuatro mil trescientos al mes en 2026.
>
> Cada uno pasa por una pre-clasificación que hoy se hace a mano y contra el
> reloj: dos días hábiles para pedir medidas de resguardo y treinta para
> investigar. Si la Inspección no se pronuncia a tiempo sobre un informe
> interno, valen las conclusiones del empleador. El atraso no es neutro.

**Por qué funciona:** abre con una cifra oficial y una consecuencia jurídica
concreta, no con la tecnología.

---

## Bloque 2 · La demo en vivo (1:35)

### 2.1 · Entrar (0:10)

**Acción:** entrar como `inspector_demo`. Cerrar la guía de bienvenida.

> Somos un inspector de la DT. A la izquierda está la cola, ordenada por
> urgencia. Todos los datos son sintéticos.

### 2.2 · Un caso nuevo, procesado en vivo (0:35)

**Acción:** «Ingreso de caso». Tipo «Denuncia directa», empleador
«Comercial Los Aromos Limitada», sector privado. Pegar el relato, marcar la
declaración y pulsar «Registrar ingreso». **Cortar la espera** en la edición
(dejar ver un segundo de «Procesando el ingreso»). Abrir el caso cuando esté
listo.

Relato para pegar (ficticio, sin datos de personas):

> Trabajo como administrativa en la oficina de una empresa ficticia desde
> marzo. Desde hace dos meses, mi jefatura me excluye de las reuniones del
> equipo, revisa en voz alta mis errores frente a todos y me dijo que si sigo
> reclamando me va a dejar sin contrato en diciembre. Ayer me tomó del brazo
> con fuerza en el pasillo para que no me fuera de la oficina. Tengo miedo de
> volver mañana.

> Ingreso un caso que el sistema no ha visto nunca. Lo seudonimiza, aplica las
> reglas y llama al modelo dos veces: una para extraer los hechos y otra para
> proponer.
>
> La propuesta no viene sola: viene con **citas literales**, resaltadas en el
> relato. El sistema verificó cada una carácter por carácter contra el texto;
> si una no calzara, la propuesta se anula.

*Solo si aparece el chip «Resguardo»:*

> Y como hubo contacto físico y una amenaza, el caso sube a urgencia de
> resguardo: es el plazo de dos días hábiles.

### 2.3 · El caso difícil: SINT-0002 (0:30)

**Acción:** abrir **SINT-0002** en la cola. Señalar la frase del relato donde se
pide conversar y llegar a un acuerdo, y luego el recorrido del caso.

> Este caso pone a prueba el diseño. Hay acoso sexual, y la persona pide que la
> citen a conversar y lleguen a un acuerdo. Lo intuitivo sería mediación, y la
> ley lo prohíbe: el artículo 211-D excluye el acoso sexual de la mediación.

*Si aparece el aviso rojo «Una regla dura corrigió al modelo»:*

> Y aquí el modelo se equivocó: propuso mediación. Una regla en código, RD-10,
> lo corrigió y dejó constancia. **La parte que no se puede equivocar no se la
> preguntamos al modelo.**

*Si no aparece:*

> El modelo propone investigar. Si hubiera propuesto mediación, una regla en
> código, RD-10, lo habría corregido y dejado constancia. **La parte que no se
> puede equivocar no se la preguntamos al modelo.**

### 2.4 · La persona decide (0:20)

**Acción:** en el caso del bloque 2.2, pulsar «Confirmar propuesta» y mostrar
el aviso de la bandeja de destino. Después señalar en la cola la tarjeta de
**SINT-0004**, con el chip «Sin IA» y la regla que lo derivó.

> Yo decido: confirmo, corrijo o descarto. Un descarte exige motivo, comentario
> y una cita, y lo valida un supervisor distinto. Nunca se descarta por falta
> de prueba.
>
> Y este caso es de un funcionario municipal: una regla lo deriva antes de
> llamar al modelo. Costó cero.

---

## Bloque 3 · Cómo lo construimos (0:40)

**En pantalla:** el diagrama del flujo en el README; luego `prompts/` y la tabla
«Mejora medida de los prompts» del README.

> Tres capas, en este orden. Primero, trece reglas duras en código, cada una
> con su test: lo que no admite interpretación no se le pregunta al modelo.
> Segundo, seudonimización antes de cualquier llamada: si queda un dato
> personal, el flujo se corta. Tercero, dos llamadas a Claude con salida
> validada y el texto literal de la ley en un prefijo cacheado.
>
> Los prompts están versionados y medidos con once casos. De la versión 2 a la
> 3, las citas verificadas subieron de 86 a 100 por ciento y el costo bajó 25
> por ciento. Y dos metas no se compensan: cero acoso sexual a mediación y cero
> falsos descartes.

---

## Cierre (0:10)

**En pantalla:** la URL pública y el repositorio.

> Ningún caso se resuelve solo. El agente propone; una persona decide.

---

## Qué no decir

- No prometer que reemplaza al funcionario. El argumento es el contrario.
- No dar cifras que no estén en `docs/MEJORA_PROMPTS.md` o en la ficha. El
  ahorro de tiempo no está medido: se mide en el piloto.
- No mostrar GKE, ClaveÚnica ni Langfuse como si funcionaran. Si se mencionan,
  es como hoja de ruta.
- No leer la pantalla en voz alta. Decir lo que la pantalla **no** muestra.
- No simular la IA con respuestas escritas a mano ni editar la propuesta.
- No pedir disculpas por lo que falta.

## Comprobación antes de subir

- Duración ≤ 3:00 (meta 2:55).
- Se ve la URL pública y la IA procesando un caso nuevo.
- No aparece ninguna contraseña, clave ni Config Var.
- El enlace del video es público o accesible para el profesor y queda en la
  tabla de entregables del README.
