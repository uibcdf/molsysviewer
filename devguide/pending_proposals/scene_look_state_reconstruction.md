# Propuesta de Mejora: Reconstrucción del Estado de "Look" de la Escena (Causa Raíz Generalizada)

## 1. Contexto y Diagnóstico

Esta propuesta **generaliza** dos propuestas existentes que describen el mismo síntoma para un
caso concreto (el color de fondo):

- [[background_color_replay_omission]] (`background_color_replay_omission.md`)
- [[background_color_persistence_gap]] (`background_color_persistence_gap.md`)

El análisis del código revela que el color de fondo **no es un caso aislado**, sino una
instancia de un hueco conceptual más amplio: **ninguna op de "look" de la escena sobrevive a un
rebuild.**

### La mecánica del rebuild

`_rebuild_view_from_current_molsys()` en `molsysviewer/viewer/core.py` (~línea 1018) borra por
completo el historial de mensajes y **reconstruye el estado desde una enumeración explícita de
categorías**, no reproduciendo `_message_history`:

```python
self._message_history = []          # ~línea 1018: se descarta todo
self._pending_messages = []
self._send({"op": "clear_all"})
self._send({"op": "load_molsys_payload", ...})
# luego reconstruye, en este orden, SOLO:
#   - representación global (whole)
#   - hide_global
#   - layers activas (+ hidden)
#   - regions activas (+ representación + hidden)
#   - _shape_history       (replay)
#   - _annotation_history  (replay)
#   - _measurement_history (replay)
#   - _selection_history   (replay)
#   - _update_visibility_in_frontend()
```

Cualquier estado que **solo viva en `_message_history`** (y no tenga ni un objeto de estado
persistente ni un historial especializado) se pierde de forma permanente en cada rebuild
(`set`, `add`, `remove`, `append_structures`).

### Ops afectadas (todas enviadas vía `_send`, sin reconstrucción)

Verificadas en `molsysviewer/scene.py` y `molsysviewer/viewer/visibility.py`:

| Op | Origen | ¿Estado persistente? | ¿Reconstruida en rebuild? |
|---|---|---|---|
| `toggle_background` / `set_background_color` | `scene.py:47,50` | No | No |
| `set_fog` | `scene.py:93` | No | No |
| `set_lighting` | `scene.py:120` | No | No |
| `set_clip_planes` | `scene.py:179` | No | No |
| `set_legend` | `scene.py:211` | No | No |
| `set_focus_fade` | `visibility.py:95,105` | No | No |

### Impacto sobre la exportación

`_build_export_messages()` (`molsysviewer/viewer/export.py`) construye la exportación a partir
del **`_message_history` actual**. Por tanto:

- **Sin rebuild previo**: estas ops sí están en `_message_history` y la exportación HTML las
  conserva correctamente.
- **Tras un rebuild**: como el rebuild ya las borró de `_message_history`, la exportación
  también las pierde.

Es decir, el agujero no está en la exportación en sí, sino en el rebuild que la alimenta.

## 2. Por qué importa (alineación con el principio rector)

El principio fundacional del proyecto (`guiding_principles.md`,
`development_mantra.md`) es que **la interacción debe convertirse en estado reproducible que
sobreviva a replay, rebuild y export**. El look de escena (fondo, iluminación, niebla, planos
de corte, leyenda, focus-fade) es estado que el científico configura deliberadamente para
preparar una figura, y **hoy se destruye ante cualquier edición estructural menor**. Esto
contradice directamente el mantra "no dejes que la interacción adelante a la reproducibilidad".

No es un bug puntual: es **estructural**. El modelo de reconstrucción enumera categorías a mano
y la categoría "scene-look" nunca se añadió.

## 3. El patrón que ya existe en el repo (a seguir)

La caja de simulación (`box`) ya resuelve este problema correctamente y debe usarse como
modelo: guarda su configuración en un atributo de estado persistente (`self._box_record`) y el
rebuild la restaura explícitamente (ver `core.py:712`). El look de escena debería seguir el
mismo patrón.

## 4. Propuestas de Solución (en orden de preferencia)

### Opción A (recomendada): Objeto de estado de look + paso de reconstrucción único

1. Añadir en `MolSysView.__init__` un único contenedor de estado de presentación, p. ej.:

   ```python
   self._scene_look: dict[str, dict] = {}   # op_key -> último mensaje enviado
   ```

2. Hacer que `SceneManager`/`VisibilityMixin` registren la última configuración de cada canal
   de look al enviarla (igual que el color de fondo propuesto en
   [[background_color_replay_omission]], pero para todas las ops de la tabla). Clave por canal
   (`background`, `fog`, `lighting`, `clip_planes`, `legend`, `focus_fade`) para que cada nueva
   llamada sobrescriba la anterior.

3. Añadir **un solo bloque** al final de `_rebuild_view_from_current_molsys` (antes de
   `_update_visibility_in_frontend`) que reenvíe `self._scene_look.values()` en orden
   determinista.

4. Garantizar su presencia en `_build_export_messages` reinyectando `self._scene_look` si el
   historial fue limpiado.

**Ventaja**: una sola fuente de verdad y un solo punto de reconstrucción; añadir un canal nuevo
de look en el futuro es trivial y no vuelve a olvidarse.

### Opción B: Historial especializado `_scene_look_history`

Replicar el patrón de `_shape_history`/`_annotation_history`: un historial dedicado que el
rebuild reproduce. Más consistente con los cuatro historiales existentes, pero introduce un
quinto historial con su propia lógica de remapeo (innecesaria aquí, porque el look de escena no
depende de índices de átomos). Menos preferible que A precisamente por eso.

### Nota sobre `focus_fade`

`set_focus_fade` depende de una selección/región de foco; al reconstruirlo hay que remapear (o
revalidar) el objetivo de foco tras el cambio de topología, o degradar con gracia si la
selección de foco ya no existe. Es el único canal de look con dependencia de índices.

## 5. Criterios de Aceptación

1. Tras configurar fondo, iluminación, niebla, planos de corte y/o leyenda, una mutación
   estructural (`view.remove(...)`, `view.append_structures(...)`, etc.) **conserva** todos
   esos ajustes sin intervención del usuario.
2. La exportación HTML tras un rebuild preserva el look de escena configurado.
3. Existe una prueba de regresión que, partiendo de una vista demo, configura varios canales de
   look, fuerza un rebuild y verifica que las ops correspondientes reaparecen en
   `_build_export_messages()` y en la secuencia enviada al frontend.
4. Añadir un canal de look nuevo en el futuro requiere registrarlo en un único sitio (no en el
   cuerpo del rebuild).

## 6. Relación con otras propuestas

Cuando esta propuesta se implemente, [[background_color_replay_omission]] y
[[background_color_persistence_gap]] quedan **subsumidas** (el color de fondo es el primer canal
del contenedor de look) y deberían cerrarse o fusionarse para evitar tres documentos
describiendo el mismo agujero a distinta granularidad.
