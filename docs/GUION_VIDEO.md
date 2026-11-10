# Guion del video · versión final

Estructura que pide la pauta: **problema → demo en vivo → cómo lo construyeron.**
Versión aprobada el 9 de noviembre de 2026: **2:32**, 1920×1080, 30 cuadros
por segundo.

| Escena | Inicio | Duración | Bloque de la pauta |
|---|---:|---:|---|
| 1 · Las cifras y el plazo | 0:00 | 20,8 s | Problema |
| 1b · «El atraso NO es neutro» | 0:21 | 9,7 s | Problema |
| 2 · Presentación de Karin Triage | 0:30 | 6,9 s | Transición |
| 3 · Caso nuevo procesado en vivo | 0:37 | 24,4 s | Demo en vivo |
| 4 · El caso difícil (SINT-0002) | 1:02 | 23,9 s | Demo en vivo |
| 5 · La persona decide | 1:26 | 19,1 s | Demo en vivo |
| 6 · Cómo lo construimos | 1:45 | 27,7 s | Cómo lo construyeron |
| 6b · Metas que no se negocian | 2:12 | 8,9 s | Cómo lo construyeron |
| 7 · Cierre | 2:21 | 10,4 s | Cierre |

## Narración

Voz «Catalina - Español Chileno» de ElevenLabs, modelo `eleven_v4`, con
dirección de voz: etiquetas entre corchetes (no se pronuncian), MAYÚSCULAS
para el énfasis y puntos suspensivos para las pausas. El texto con sus
etiquetas está en [`video/narracion.json`](video/narracion.json).

1. En veintitrés meses de Ley Karin, la Dirección del Trabajo recibió…
   noventa y dos mil seiscientos cuarenta y tres ingresos. Más de cuatro mil
   trescientos… al mes. Y cada uno se clasifica a mano, contra el reloj: dos
   días hábiles para pedir medidas de resguardo. Treinta… para investigar.
2. Si la Inspección no se pronuncia a tiempo sobre un informe interno, valen
   las conclusiones del empleador. El atraso no es neutro.
3. Presentamos… Karin Triage. El agente propone. Una persona decide.
4. Llega una denuncia que el sistema nunca ha visto. Karin Triage seudonimiza
   el relato, aplica las reglas de la ley y le pide a Claude una propuesta. En
   segundos: procede investigar, por acoso laboral. Cada afirmación se apoya
   en una cita literal, verificada carácter por carácter contra el texto. Y
   como hubo contacto físico y una amenaza, el caso sube a urgencia de
   resguardo.
5. Ahora, el caso difícil: acoso sexual, y la persona pide conversar y llegar
   a un acuerdo. Pero la ley es clara: el acoso sexual no va a mediación. El
   agente propone investigar. Y si se equivocara, una regla escrita en código
   corrige la decisión y deja constancia. Lo que no se puede equivocar, no se
   le pregunta al modelo.
6. La última palabra es siempre humana: confirmar, corregir o descartar. Un
   descarte exige motivo, cita y la firma de un supervisor. Y lo que la ley
   resuelve sola, como la denuncia de un funcionario municipal, ni siquiera
   llega al modelo. Costo… cero.
7. ¿Cómo lo construimos? Tres capas, en este orden. Trece reglas duras en
   código, cada una con su prueba. Seudonimización antes de cualquier
   llamada. Y dos llamadas a Claude, con salida validada y la ley citada al
   pie de la letra. Medimos cada versión del prompt: de la versión dos a la
   tres, las citas verificadas pasaron de ochenta y seis… a cien por ciento,
   y el costo bajó un veinticinco por ciento.
8. Y dos metas que no se negocian: cero casos de acoso sexual a mediación.
   Cero falsos descartes.
9. Karin Triage. Ningún caso se resuelve solo. El agente propone… una persona
   decide.

Todas las cifras salen del informe DT con corte al 30 de junio de 2026 y de
[`MEJORA_PROMPTS.md`](MEJORA_PROMPTS.md). El ahorro de tiempo no se afirma:
se mide en el piloto.

## Demo en vivo

Las tomas de la app se grabaron el 9 de noviembre de 2026 en la URL
publicada, con una tanda nueva y un caso ingresado en ese momento. La
propuesta que se ve es la respuesta real del modelo:

- **Caso nuevo:** «Procede investigación por acoso laboral», urgencia de
  resguardo y 3 de 3 citas verificadas.
- **SINT-0002:** el modelo propuso investigar; RD-12 elevó la urgencia. RD-10
  no tuvo que corregir, y la narración lo dice así.
- **Decisión:** «Confirmar propuesta» y aviso «pasó a Revisados». SINT-0004
  (municipal) aparece sin IA.

El relato del caso nuevo es ficticio y no contiene datos de personas. La
sesión la inició una persona del equipo; el script de grabación nunca escribe
contraseñas.

## Sonido

- **Música:** pista electrónica generada con ElevenLabs Music, con el primer
  drop alineado a «El atraso NO es neutro». Baja bajo la voz.
- **Efectos:** unos 115, generados con ElevenLabs (whoosh, pop, impacto, ding,
  ticks, tecleo y clics), cada uno en el instante en que aparece o desaparece
  un elemento. También bajan bajo la voz.
- **Mezcla:** −15 LUFS integrados, pico real −1,3 dBTP, sin recortes.

## Cómo reproducirlo

Desde la raíz del repositorio. Las claves se leen de `~/.config` y la sesión
de `~/.cache`, fuera del repositorio. Las salidas quedan en
`docs/video/salida/`, que no se versiona.

```bash
uv run --no-project --with playwright python docs/video/grabar_demo.py sesion
uv run --no-project --with playwright python docs/video/grabar_demo.py preparar
uv run --no-project --with playwright python docs/video/grabar_demo.py grabar ingreso sint0002 decidir
uv run --no-project python docs/video/montaje/construir.py
uv run --no-project --with playwright python docs/video/montaje/render.py docs/video/salida/montaje.json docs/video/salida/video-sin-audio.mp4
uv run --no-project --with numpy python docs/video/montaje/construir.py --audio
```

La narración, la música y los efectos se generan aparte con la API de
ElevenLabs y quedan en `docs/video/salida/voz/`, `musica-electronica.mp3` y
`sfx/`. Las tomas pasan a fotogramas clave en `salida/intra/` antes de
renderizar.
