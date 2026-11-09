# Plan de diseño · rediseño con identidad DT

> Nota posterior: `/demo/nuevo` pasó a `/ingresos/nuevo` («Ingreso de caso») y el
> perfil «analista» a «inspector». Las secciones 0–7 se conservan como se
> aprobaron; los cambios posteriores están en la sección 8.

Fecha: 2026-11-08. Alcance: las cinco pantallas de la bandeja (`/entrar`, `/`,
`/casos/{id}`, `/demo/nuevo`, estado en vivo de la bandeja y del caso). Las
páginas estáticas (`ficha-negocio.html`, `diagramas-karin-triage.html`) quedan
fuera de este plan.

Fuentes:
- Normas gráficas: artefacto «DT Redes Sociales»
  (`https://claude.ai/artifact/GdxbzjpGeD7QeGvbeWnPug`), archivos
  `project/README.md`, `project/tokens.json`, `project/assets/*/README.md` y
  `project/components/*/README.md`, leídos el 2026-11-08.
- Apple Human Interface Guidelines, leídas el 2026-11-08 en
  `developer.apple.com/design/human-interface-guidelines/`: *Layout*, *Feedback*,
  *Loading*, *Motion* y *Accessibility*.
- Código actual: `backend/src/karin_triage/api/estaticos/estilo.css` (22 líneas)
  y `api/plantillas/*.html`.

Capturas «antes» en `docs/capturas/antes/`: `bandeja-1440.jpg`,
`bandeja-800.jpg`, `bandeja-375.jpg` y `caso-1440.jpg`.

## 0. Advertencias antes de diseñar

1. **Las normas son para redes sociales, no para web.** El sistema define
   stories de 1080 × 1920 y posts de 1080 × 1350, con medidas en píxeles de ese
   canvas, y dice: «No mezcles los recursos de un formato con los del otro, y no
   inventes otros motivos decorativos». Para una web hay que **traducir** las
   normas: paleta, tipografías, temas, esquinas, tarjetas, logo y cinta se usan
   tal cual; la escala tipográfica se reduce a tamaños de pantalla. Lo que no
   tiene equivalente (cápsula de story, barra lateral, línea vertical) **no se
   usa**, para no inventar motivos.
2. **Licencia de las tipografías: `PENDIENTE_VERIFICAR`.** Museo Sans y Museo
   Sans Display son fuentes comerciales. Servirlas desde un sitio público exige
   una licencia web, y no pude confirmar que la DT o el equipo la tengan. La
   licencia de gobCL tampoco está verificada. Ver la decisión D1.
3. **Riesgo de suplantación.** Por tu decisión, la identidad de la DT se usa sin
   modificaciones, con una franja visible que dice que es un prototipo académico.
   El plan **no** usa la firma «GOBIERNO DE CHILE · DIRECCIÓN DEL TRABAJO» del
   footer de post, porque sumada al logo presenta el sitio como un servicio
   oficial. Ver la decisión D2.

## 1. Brechas frente a las normas de la DT

| Elemento | Norma (artefacto) | Estado actual | Brecha | Propuesta |
|---|---|---|---|---|
| Paleta | 14 colores oficiales: `navy` #25306B, `cobalt` #193A97, `signal-blue` #005DFF, `emblem-blue` #006BB9, `emblem-red` #FF1D3D, `mist` #EDF0F5, `ice` #CFE2FF, `blush` #FDD1D5, etc. | `#182b39`, `#245877`, `#174a70`, `#f5f7f8`, `#a15b00`, `#8a3a00`, `#fff4e5` (`estilo.css:1-21`) | Ningún color de la paleta | Tokens CSS con los nombres oficiales y tokens de uso (`--fondo`, `--texto`, `--tarjeta`…) |
| Tema | Navy para «Formales: normativa, comunicados»; Gris para «Mucho texto, tablas, datos»; Rojo para «Alertas, plazos, urgencias» | Sin tema | — | Encabezado en tema **Navy** (`navy` → `cobalt`) con logo; contenido en tema **Gris** (`white`/`mist`, texto `navy`); urgencia con los colores del tema **Rojo**, sin fondos rojos con texto chico |
| Tipografía | Museo Sans 500 como regular, 700 de énfasis, 900 en títulos; Museo Sans Display 1000 solo para una cifra por pieza; gobCL solo en firmas | `system-ui` | Ninguna fuente de marca | Inter (Google Fonts) con los pesos de la norma y `system-ui` de respaldo (D1). Una sola cifra protagonista en la bandeja, en Inter 900: casos pendientes. gobCL no se usa |
| Escala | Canvas de 1080 px: `cuerpo` 32/44, `nota` 26/36 como mínimo, `titulo-m` 56/64 | Tamaños del navegador | No hay escala | Escala web proporcional: `cuerpo` 16/24 (500), `nota` 14/20 (mínimo), `bajada` 20/28, `titulo-m` 28/34 (900), `titulo-l` 36/42, `titulo-caps` 13/20 (900, +0,02em), `etiqueta` 12/16 (900, +0,04em), `cifra` 56/56 Display |
| Logotipo | `logo-dt.svg` «tal cual, sin recolorear, recortar ni separar el escudo del texto» | Texto «Karin Triage» | Sin logo | `logo-dt.svg` copiado desde el artefacto, sin cambios, en el encabezado, con el nombre del producto al lado y separado |
| Esquinas y sombras | «Las esquinas son rectas (`radius-recto`) en todo menos la cápsula. No uses sombras.» | Botones y campos con los valores del navegador | — | `border-radius: 0` en botones, campos, tarjetas y tablas; sin `box-shadow` |
| Tarjetas | `tarjeta` = `ice` con texto `navy`, relleno `space-4`, sin bordes ni sombras | No hay tarjetas | — | La propuesta, las citas y el historial del caso van en tarjetas `ice`; las secundarias en `pale-sky`/`powder` |
| Contingencia | `CintaContingencia` marca alertas y urgencias; nunca lleva texto encima | `⚠ Urgencia de resguardo` en negrita | Sin recurso de marca | `cinta-contingencia-dark.svg` (tema Gris) sobre la ficha de los casos con `urgencia_resguardo`, más la etiqueta de texto. La cinta no reemplaza el texto |
| Espaciado | Pasos de 8 px (`space-1` a `space-12`) | `rem` sueltos | — | Los mismos pasos, divididos a la mitad para web cuando haga falta (4/8/12/16/24/32/48) |
| Iconografía | «No uses emoji ni íconos genéricos como decoración» | `⚠` en urgencia (`_fila.html:3`, `caso.html:9`) | Emoji como señal | Reemplazar `⚠` por una etiqueta tipográfica «URGENCIA» en estilo `etiqueta` |
| Tono | Directo, en segunda persona, sin jerga | «procesados: 3, saltados: 8», «Revisión histórica · fundamento de descarte no capturado; usar nueva tanda», «Sin referencia» | Jerga interna | Reescritura de microcopia (sección 5) |

## 2. Principios de las Apple HIG aplicables a una web

Cada principio se resume desde su fuente oficial y se baja a un cambio concreto.

| Principio | Fuente HIG | Qué dice (resumen) | Aplicación aquí |
|---|---|---|---|
| Jerarquía | *Layout* › Visual hierarchy | Ordenar el contenido por importancia relativa, con lo más importante arriba y al inicio; agrupar lo relacionado; divulgación progresiva | Bandeja: primero la cifra de pendientes y los casos urgentes, luego el resto. Caso: decisión y urgencia arriba, después el relato, las citas y las reglas. Las tandas antiguas quedan en un `<details>` «Historial de tandas anteriores» |
| Claridad | *Layout*: diferenciar controles del contenido | Distinguir los controles del contenido | Botones `signal-blue` rectos con texto `white` (5,24:1); el contenido queda en tarjetas `ice` |
| Retroalimentación | *Feedback* | Informar el estado actual y el éxito o fracaso de una acción; mostrar el estado cerca de lo que describe; usar alertas solo para lo crítico; explicar por qué algo no se pudo hacer | Estado de carga junto a la bandeja, confirmación en la fila revisada y mensajes de bloqueo con la razón (ya existen; se reubican y se reescriben) |
| Carga | *Loading* | Mostrar algo cuanto antes; dejar que la persona siga haciendo otras cosas; indicador determinado si se conoce la duración, indeterminado si no | `/demo/nuevo` muestra un indicador indeterminado mientras corre la IA. La carga de una tanda muestra un indicador determinado (procesados/total) |
| Movimiento | *Motion* | Movimiento con propósito, nunca por agregarlo; animaciones breves y precisas; evitar animar interacciones frecuentes; no hacer esperar a que termine una animación | Catálogo cerrado de 5 animaciones (sección 3). No hay animación al navegar entre bandeja y caso, porque es la interacción más frecuente |
| Accesibilidad | *Accessibility* | Contraste mínimo WCAG AA: 4,5:1 hasta 17 pt y 3:1 desde 18 pt o en negrita; no comunicar solo con color; uso completo con teclado; responder a «Reducir movimiento» | Sección 4 |

## 3. Catálogo de animaciones

Regla de entrada: cada animación cumple una de tres funciones, carga,
transición de estado o confirmación. Con `prefers-reduced-motion: reduce`, todas
se reemplazan por un cambio instantáneo y el texto de estado sigue visible. El
texto, nunca la animación, lleva la información (HIG *Motion*: «Make motion
optional»).

Curvas: entrada `cubic-bezier(0.2, 0, 0, 1)` (desaceleración), salida
`cubic-bezier(0.4, 0, 1, 1)`, indeterminada `linear`.

| # | Dónde | Función | Qué se mueve | Duración y curva | Con movimiento reducido |
|---|---|---|---|---|---|
| A1 | `/demo/nuevo`, al enviar | Carga | El botón se desactiva y muestra «Procesando con IA…»; debajo, una barra indeterminada de 3 px en `signal-blue` sobre `ice` | Aparece en 150 ms con la curva de entrada; la barra recorre en 1,2 s `linear` en bucle hasta la respuesta | Sin barra; el texto «Procesando con IA…» queda fijo |
| A2 | Bandeja, carga de golden set o tanda nueva | Carga (determinada) | Barra de progreso: ancho = procesados/total | 300 ms de curva de entrada en cada actualización (cada 5 s) | El ancho cambia sin transición; el texto «4 de 11 casos procesados» siempre visible |
| A3 | Bandeja, aparece un caso nuevo tras el sondeo | Transición de estado | Fondo de la fila nueva de `ice` a transparente | 1,2 s de curva de salida, una sola vez | Sin fundido; etiqueta «NUEVO» estática hasta el siguiente sondeo |
| A4 | Caso, revisión registrada (respuesta 2xx de htmx) | Confirmación | La fila de estado cambia y aparece «Revisión registrada» con fundido + desplazamiento de 4 px | 200 ms de curva de entrada | Aparece sin movimiento; el texto se anuncia con `role="status"` |
| A5 | Caso, revisión rechazada (4xx) | Confirmación de error | El aviso `#aviso-revision` aparece con fundido | 150 ms de curva de entrada; sin sacudidas | Aparece sin movimiento; se anuncia con `role="alert"` (ya existe) |

Descartadas a propósito:
- Transición entre bandeja y caso: es una interacción frecuente (HIG *Motion*).
- Animar la cinta de contingencia o hacer parpadear la urgencia: la norma no lo
  contempla y una oscilación sostenida molesta.
- Indicador animado del sondeo cada 5 s: es frecuente y no cambia el estado.
  Se reemplaza por el texto fijo «Actualizado a las HH:MM:SS».

Implementación: CSS puro (`@keyframes` y `transition`) más clases que htmx ya
pone (`htmx-request`, `htmx-added`, `htmx-settling`). No se agregan librerías.

## 4. Limpieza de UX incluida (ítem 4 del plan de entrega)

Solo cambios de plantillas y de `api/main.py`, **sin tocar el esquema ni las
migraciones**:

1. **Bandeja con la tanda vigente por defecto.** La tanda se reconoce por el
   prefijo `DEMO-<tanda>-` de `id_externo_dt` (`api/main.py:276-281`). Se muestra
   la tanda más reciente y los relatos nuevos (`DEMO-<12 hex>`); el resto queda
   en un `<details>` cerrado. No se borra nada.
2. **Login con contexto:** qué es, para quién, que solo usa datos sintéticos, y
   que las credenciales se entregan por la plataforma del curso.
3. **Ficha del caso:** «Motivo de descarte» solo aparece si la decisión es
   `DESCARTADO` (`caso.html:10`); en las citas, la referencia solo aparece si
   existe (`caso.html:23`); «Fuente: denuncia/normativa» pasa a etiqueta.
4. **Microcopia:**
   - «procesados: 3, saltados: 8, fallidos: 0» → «Carga terminada: 3 casos nuevos, 8 ya estaban en la bandeja».
   - «Revisión histórica · fundamento de descarte no capturado; usar nueva tanda» → «Revisión de una versión anterior (sin fundamento registrado)».
5. **Móvil (< 640 px):** la tabla de 8 columnas hoy desborda (874 px de
   contenido en 353 px de ancho, medido con 375 × 812). Pasa a una lista de
   tarjetas con caso, propuesta, urgencia y estado.
6. **Accesibilidad estructural:** enlace «Saltar al contenido», `<nav>` y
   `<footer>`, `aria-live="polite"` en la bandeja viva y `scope="col"` en los
   encabezados de la tabla.
7. **Franja de prototipo** (decisión de la fase 0), visible en todas las
   páginas, arriba del encabezado: «Prototipo académico UAI · no es un servicio
   de la Dirección del Trabajo». Fondo `mist`, texto `navy` (10,73:1).

No incluido: el historial de prueba de SINT-0002 («Verificación técnica con
caso sintético») queda en la base porque borrarlo es un borrado de datos. Con
el filtro del punto 1 deja de verse por defecto.

## 5. Verificación

### Contraste WCAG AA (calculado con la fórmula de luminancia relativa de WCAG 2.x)

| Par | Ratio | Uso | Resultado |
|---|---:|---|---|
| `navy` sobre `white` | 12,25:1 | Texto principal | AA |
| `navy` sobre `mist` | 10,73:1 | Franja de prototipo, fondo de página | AA |
| `navy` sobre `ice` | 9,32:1 | Tarjetas | AA |
| `navy` sobre `blush` | 8,90:1 | Etiqueta de urgencia | AA |
| `cobalt` sobre `white` | 10,03:1 | Texto secundario | AA |
| `white` sobre `navy` | 12,25:1 | Encabezado | AA |
| `white` sobre `signal-blue` | 5,24:1 | Botones | AA |
| `signal-blue` sobre `white` | 5,24:1 | Enlaces | AA |
| `signal-blue` sobre `mist` | 4,58:1 | Enlaces sobre fondo de página | AA (justo) |
| `emblem-red` sobre `white` | 3,82:1 | Solo bordes y la barra de urgencia, nunca texto | AA para no texto (≥ 3:1) |
| `white` sobre `emblem-red` | 3,82:1 | **No se usa** con texto menor a 24 px | — |
| `signal-blue` sobre `ice` | 3,98:1 | **No se usa** para texto | — |

Anillo de foco: 3 px `signal-blue` con 2 px de separación sobre fondos claros
(5,24:1) y 3 px `white` sobre el encabezado `navy` (12,25:1).

### Teclado

Recorrido completo sin ratón, con evidencia por pantalla:
- `/entrar`: usuario → contraseña → Entrar.
- Bandeja: saltar al contenido → acciones → enlaces de casos → `<details>` del historial.
- Caso: volver → formulario de revisión → registrar.
- `/demo/nuevo`: relato → casilla → enviar.

Se verifica que el foco siempre sea visible, que el orden siga la lectura y que
no haya trampas de foco. Se prueba en el navegador integrado con `Tab` y se
deja constancia escrita del recorrido.

### Movimiento reducido

Emular `prefers-reduced-motion: reduce` y comprobar que A1–A5 no animan y que
su texto sigue visible.

### Capturas antes y después

Las mismas cuatro vistas (bandeja 1440, bandeja 800, bandeja 375 y caso 1440),
más login y `/demo/nuevo`, en `docs/capturas/despues/`. El login «después» se
captura en local, para no cerrar tu sesión en producción.

### Pruebas

`pytest` completo antes de cualquier despliegue, con su salida a la vista. Se
agregan pruebas de: filtro de tanda vigente, ocultar «Motivo de descarte» fuera
de `DESCARTADO`, presencia de la franja de prototipo y del enlace «Saltar al
contenido».

## 6. Archivos que cambian

- `api/estaticos/estilo.css`: reescrito con tokens.
- `api/estaticos/logo-dt.svg` y, si apruebas D1, `api/estaticos/fuentes/*.otf`:
  nuevos, copiados del artefacto sin modificar.
- `api/estaticos/cinta-contingencia-dark.svg`: nuevo, copiado del artefacto.
- `api/plantillas/*.html`: estructura, microcopia y clases.
- `api/main.py`: filtro de tanda vigente y textos de estado.
- `backend/tests/`: pruebas nuevas.

Sin dependencias nuevas, sin cambios de esquema y sin migraciones.

## 7. Decisiones abiertas

- **D1 · Tipografías. Resuelta (2026-11-08):** se usa **Inter** desde Google
  Fonts, con los pesos de la norma (500 regular, 700 énfasis, 900 títulos y
  cifra), y `system-ui` como respaldo. Museo Sans no se sirve.
- **D2 · Firma de gobierno.** Recomendación: no usar el footer «GOBIERNO DE
  CHILE · DIRECCIÓN DEL TRABAJO» y usar solo el logo, más la franja de
  prototipo.
- **D3 · Esfuerzo.** Estimado en 5–7 h para el rediseño y 2–3 h para la
  limpieza de UX, pruebas y capturas incluidas.

## 8. Cambios posteriores aprobados (2026-11-08)

Decisiones del responsable del proyecto que se apartan de la norma gráfica de
redes sociales de la DT, aplicadas a la interfaz web:

- **Formas redondeadas.** La norma pide esquinas rectas salvo la cápsula. La
  interfaz usa cápsulas en botones, chips, pestañas y opciones, y cajas de
  puntas redondeadas (18 px) en tarjetas, paneles y avisos. Tokens
  `--radio-capsula`, `--radio-caja`, `--radio-control` y `--radio-chico`.
- **Iconos.** La norma no tiene un set de íconos. La interfaz usa un sprite SVG
  propio de trazo (`plantillas/_sprite.html`), con varios iconos en el estilo y la
  geometría de Lucide (licencia ISC). No se agregó ninguna librería. Los iconos
  acompañan siempre un texto; no hay botones que solo tengan un icono.
- **Perfil «inspector».** El perfil de primera revisión se llama inspector
  (usuario `inspector_demo`). La contraseña sigue en la Config Var
  `KARIN_DEMO_PASSWORD_ANALISTA` para no cambiar la configuración publicada. Las
  revisiones guardadas antes del cambio conservan `analista_demo` como
  funcionario y su rol se muestra como «inspector».
- **Ingreso de caso.** El antiguo «Probar la IA con un relato sintético»
  pasa a «Ingreso de caso» (`/ingresos/nuevo`), con los campos que el sistema
  procesa: tipo de ingreso, fecha, empleador, sector y relato. Folios
  `ING-<12 hex>`. No se piden nombre, RUT ni contacto de quien denuncia: el
  sistema no guarda identidades (regla 2). La declaración de que no hay datos
  personales reales sigue siendo obligatoria. La franja superior y el pie de
  página son los lugares donde la interfaz declara que los datos son sintéticos.
- **Pie de página** con marca, accesos de la plataforma, enlaces del proyecto y
  normativa, y la declaración legal del prototipo, en todas las páginas.
- **Animaciones en toda la interfaz** (pedido del responsable; amplía el
  catálogo A1–A9, que se limitaba a estados del flujo):
  entrada escalonada al cargar (encabezado, cola, métricas que cuentan hasta
  su valor, pestañas, tarjetas, bloques del ingreso y pie), cascada de las
  secciones del panel en cada caso, chips que aparecen, citas que se
  «subrayan» al abrir, recorrido que dibuja su línea, tarjetas que se levantan
  al pasar, botones que responden al presionar, iconos que se desplazan,
  chevrones que giran, submenús y diálogos que aparecen con escala y avisos
  que entran desde la derecha. Las entradas solo corren al cargar la página;
  el refresco de la cola cada 5 s no las repite. Todo se anula con
  `prefers-reduced-motion`.
- **Botones ajustados al texto**: altura mínima de 44 px (36 px en los chicos),
  sin ancho mínimo fijo, texto en una línea y centrado en ambos ejes. Los
  enlaces «Volver» son botones secundarios. Verificado con una medición del
  centro del texto contra el centro de cada botón en escritorio y móvil.
- **Menú principal** en el encabezado (Bandeja, Ingreso de caso, Cómo usar,
  Proyecto y Normativa, con la sesión al final). En pantallas angostas se
  pliega tras el botón «Menú».
- **Bandeja sin caso preseleccionado** y **guía de bienvenida** por rol: tres
  pasos, menos de 60 palabras (se lee en menos de 15 segundos). Se muestra una
  vez por sesión y se reabre desde «Cómo usar».
- **Grilla común y segunda pasada HIG** (*Layout* y *Feedback*): encabezado,
  franja, contenido y pie comparten ancho máximo (96rem) y márgenes (24 px);
  medido a 1440 px, todos los bordes quedan en x=24 y x=1416, y los elementos
  del encabezado comparten el centro vertical. La cola pasa a una barra
  lateral: resumen con una cifra y una lista breve, y bandejas como lista con
  el contador a la derecha. En el panel queda una sola caja de color (la
  corrección por regla dura, en tono informativo). La urgencia es un chip con
  una línea, la advertencia RD-10 aparece al corregir o al validar una
  excepción, y la nota del descarte vive en su formulario.
