# Propuesta post-1.0: transporte binario de coordenadas (anywidget / ipywidgets buffers)

**Estado:** post-1.0
**Origen:** propuesta del colaborador (2026-07-12), verificada y aceptada en principio.
**Dependencia upstream:** ninguna. `anywidget` se apoya en `ipywidgets`, que ya soporta
buffers binarios.

## Contexto

**Hoy no hay transporte binario.** Verificado el 2026-07-12: cero apariciones de
`buffers`, `Float32Array`, `memoryview`, `tobytes` o `ArrayBuffer` en la ruta del
payload (`viewer/load.py`, `widget.py`).

Las coordenadas de una trayectoria viajan **como texto JSON**. Para un sistema de 50.000
átomos y 1.000 frames son 150 millones de números serializados a texto, transmitidos y
parseados. El coste no está en la red (el kernel suele ser local) sino en **serializar y
parsear**, en los dos extremos.

## La propuesta

`ipywidgets` transporta buffers binarios junto al mensaje JSON. Se puede enviar un
`numpy.ndarray` (o un `memoryview`) de coordenadas y recibirlo en JS **directamente como
`Float32Array`**, sin parseo intermedio.

- Python: las coordenadas salen como `float32` contiguo, en el buffer del mensaje.
- TypeScript: llegan como `ArrayBuffer` → `Float32Array`, que es **exactamente el
  formato que Mol\* quiere** para construir su modelo.

El JSON queda para la estructura del mensaje (la topología, los tags, las opciones); el
buffer, para lo que es masivo y homogéneo: **las coordenadas**.

## Por qué es post-1.0

No es un defecto: es una optimización. La 1.0 tiene que cerrar deuda (los objetos de
escena, la reproducibilidad, el undo), y esto no bloquea a nadie — hace lento lo que ya
funciona.

Pero conviene tenerlo escrito porque **cambia la frontera Python↔TS**, y quien la toque
antes debería saber que va a moverse.

## Lo que hay que medir antes de comprometerse

- **Dónde está realmente el cuello de botella.** Puede estar en el parseo (que esto
  arregla), en la construcción del modelo de Mol\* (que no), o en la conversión desde
  MolSysMT (tampoco). **Medir antes de optimizar**; el rework ya pagó un peaje de ~3
  segundos por mensaje que resultó no estar donde se suponía.
- **`float32` frente a `float64`.** Las coordenadas en `float32` pierden precisión. Para
  *dibujar* es irrelevante (Mol\* renderiza en `float32` de todos modos), pero hay que
  asegurarse de que **ninguna medida ni cálculo científico se derive del dato
  transportado** en vez de del `_molsys` de Python. Con Contract S1 esto ya está
  garantizado —Python es el dueño de los números— pero conviene decirlo, porque es
  justo el atajo que alguien tomaría.
- **El export HTML y el popup.** Ambos replayan `_message_history`. Un mensaje con buffer
  binario tiene que poder **serializarse a un HTML estático**, y eso no es gratis: habría
  que decidir si el export sigue usando JSON (más simple, y ya funciona) o embebe el
  binario en base64.

## Relación con otras propuestas

- `standalone_performance_and_depythonization.md` — la estrategia larga (Rust/WASM).
  Esto es el escalón barato que la precede.
- Los benchmarks (`devguide/benchmarks/`) son el sitio donde se demuestra que hacía
  falta.
