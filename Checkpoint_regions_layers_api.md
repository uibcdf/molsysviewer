# MolSysViewer — Regions & Layers API (Checkpoint)

## Naming & Concepts
- **Region**: subset of the molecular structure (Mol* component). Identified by a `tag` (user or auto). Holds selection string and atom indices.
- **Layer**: group of non-structural visuals (shapes/overlays: spheres, alpha-spheres, pockets, channels, labels, etc.). Identified by a `tag`.
- Tags: user-provided if given; otherwise auto-generated (`region1`, `layer1`, ...).

## Public API Sketch (Python)
- `view.new_region(selection: str, tag: Optional[str] = None, representation: Optional[str] = None, **repr_params) -> Region`
- `view.new_layer(kind: str, tag: Optional[str] = None, **kwargs) -> Layer` (created implicitly by shape helpers too).
- `view.regions` / `view.layers`: read-only mappings `{tag: Region}` / `{tag: Layer}` (usable as `view.regions["set1"].hide()`).
- Helpers: `view.get_region(tag)`, `view.get_layer(tag)`, `view.list_regions()`, `view.list_layers()`.
- `Region` methods: `set_representation(type, **params)`, `hide()`, `show()`, `delete()`, selection ops (`extract_subregion`, `add_atoms`, `remove_atoms`), `new_complementary_region()`.
- `Layer` methods: `hide()`, `show()`, `delete()`, `relabel(new_tag)`, `merge(other_layer)`.
- `Global`: `view.global_view` provides `set_representation(...)`, `show()/hide()` for whole-structure control (no tag, non-deletable).
- Complements: `new_region(..., complement_of_regions=["tagA", ...] | "all")` builds complement on Python side; requires a loaded system and known `atom_indices` from regions/acks.

## JS Side Responsibilities
- Source of truth for Mol* refs. Maintain registries:
  - Regions: `tag -> { componentRef, representationRefs[], atomIndices[], selection }`.
  - Layers: `tag -> { refs: StateObjectRef[], types: [...], count, meta }`.
- Apply selections via `component.fromSelection`; build representations per tag.
- Shapes/overlays: assign tag to transforms and store refs; existing `tagIndex` can be extended for layer registry.
- On structure reload/clear: purge registries and notify Python to invalidate mirrors.
- Expose acks/messages so Python mirrors stay in sync (tags, indices, counts).

## Behavior Notes
- Different visual styles for different atoms → create multiple regions (one selection per style).
- A layer created from a batch (e.g., alpha-spheres) groups all its refs under one tag; single shapes also form a layer.
- Users can regroup layers by re-tagging/merging (update refs’ tags).

## Defaults & Generation
- Auto tags if none provided (`regionN`, `layerN` counters on Python side).
- Dictionaries are public, functional registries for user access; mutations happen through Region/Layer methods (send messages to JS).

## Pending Implementation
- Message schema Python→JS for creating/updating regions and layers, with tag and selection/indices.
- Ack path JS→Python carrying finalized atom indices (for regions) and object metadata (for layers).
- Reset/clear hooks to invalidate both registries.

## Implementation Plan (proposed)
1. **Python skeleton**
   - Add `Region`/`Layer` wrappers.
   - Add `view.new_region(...)`, `view.new_layer(...)`, and `view.regions`/`view.layers` mappings with auto tags.
   - Stub methods on Region/Layer (`show/hide/delete/set_representation`, `relabel/merge`, etc.) that emit messages (no backend logic yet).
2. **Messaging contract**
   - Define new ops Python→JS: create/update/delete/hide/show for regions and layers; set representation for a region.
   - Define acks JS→Python: region/layer creation with indices/meta, registry cleared on reset/load.
3. **JS controller**
   - Maintain registries: regions (`tag -> componentRef, reprRefs, atomIndices, selection`) and layers (`tag -> refs, types, count`).
   - Implement handlers for the new ops using `component.fromSelection`, representation builder, and existing shape tagging for layers.
   - Tie into `clear_all/reset/load` to purge registries and notify Python.
4. **Sync & state in Python**
   - On acks, populate `view.regions`/`view.layers` mirrors (selection, atom_indices, types, counts).
   - Invalidate mirrors on reset/load.
5. **Tests**
   - Python: API/tag generation, registry updates, message construction.
   - JS/manual: new message handlers create/show/hide/delete as expected in Mol*.

## Current Status (this branch)
- Python API: `new_region` (supports complements via `complement_of_regions` or `Region.new_complementary_region`), `new_layer`, `view.global` wrapper (`set_representation` re-shows if hidden), public registries `regions`/`layers`. Regions store `atom_indices` from ack or selection; complement logic computed in Python (requires loaded system).
- JS controller: handlers for regions/layers/global (create/set/show/hide/delete), registries (`regionIndex`, `layerMeta`, `globalReprs`), `clear_all` resets and notifies. Layers auto-registered for shapes by tag.
- Messaging: acks for regions/layers; registry cleared notification. Bundle rebuilt.
- Docs: checkpoint updated; docstrings note load requirement and complement behavior; global shows on set_representation.

## Remaining items
- Optional: expose helpers (`get_region`, `get_layer`, listing) and tighten docs/tutorials.
- Optional: persist global style across reload (reapply after load).
- Optional: JS handler for selection strings (if we want region creation without precomputed indices).
- Tests: add unit coverage for complement logic, tag generation, and message construction; manual/auto smoke test with Mol* frontend.

## Visibilidad (global vs regiones vs viewer)
- `region.hide()/show()`: sólo afecta a esa región. El estado `hidden` se recuerda; `viewer.show()` no reactivará regiones ocultas.
- `global_view.hide()/show()`: afecta sólo a la representación base/global (auto/preset/cartoon cargada al `load`). No toca regiones. Si se invoca antes del primer `show()`, la intención se memoriza y se aplica al cargar la estructura.
- `viewer.hide()/show()` con `selection="all"`: ajusta la máscara de átomos y envía `hide_global/show_global target=all`. Respeta regiones ocultas y re-oculta la vista global si estaba marcada como oculta.

### Flujos de referencia (manual/UI)
1) **Ocultar global antes de mostrar**
```python
view = viewer.demo.tctim
view.global_view.hide()
view.show()  # se muestran sólo las regiones creadas; la base/global permanece oculta
```
2) **Ocultar región y mantenerla oculta tras hide/show general**
```python
view = viewer.demo.tctim
r1 = view.new_region("chain_id == 'A'", representation="sticks")
r2 = view.new_region("chain_id == 'B'", representation="sticks")
r2.hide()
view.hide(); view.show()  # r1 visible, r2 sigue oculta; global según su estado previo
```
3) **Ocultar todo y reactivar sólo lo visible**
```python
view.hide()  # oculta global + regiones + máscara de átomos
view.show()  # reactiva máscara; regiones ocultas permanecen ocultas; global según flag
```

## Considerations / Future Improvements
- Coexistencia de representaciones: hoy las regiones añaden reps sin remover las previas, y global es independiente. Podría ser útil ofrecer modos “replace” (elimina reps globales/preset antes de aplicar región) o “exclusive” (desactiva otras reps solapadas) para evitar solapes visuales confusos.
- Selección por string en JS: dependemos de `atom_indices` precomputados; si `_molsys` no está o se quiere crear regiones desde el frontend, convendría aceptar `selection` string (query Mol*) en el handler como fallback.
- Sincronización inversa: si el usuario añade/borra reps directamente en Mol* (u otro módulo), el registro Python no se entera. Habría que emitir eventos JS→Py de cambios en el state tree para mantener contabilidad exacta.
- Persistencia del estilo global: `set_global_representation` re-muestra si estaba oculto, pero tras un `load` se pierde el estilo salvo que el usuario lo reaplique. Guardar el último estilo global y reenviarlo tras cada carga.
- Visibilidad coordinada: `hide/show` de regiones/layers usan `isHidden`; la máscara de visibilidad global (opacidad) es otra vía. Un método para combinarlas o exponer el estado efectivo ayudaría a evitar confusión.
- Metadatos de layers: registrar más info (tipos/colores/params) para inspeccionar qué contiene cada layer sin rehacer la escena; eventualmente un inspector UI.
- Ergonomía de API: helpers `get_region/get_layer/list_*`, autocompletado; métodos en `Layer` para merge/split/re-tag refs si se reagrupan.
- Validación/errores: en complementos, si alguna región no tiene `atom_indices` (ack pendiente) se excluye mal. Bloquear hasta tener índices válidos o recalcular en Python y surfacing de errores claro.
- Interacción con visibilidad parcial: las regiones no tocan la máscara; si el usuario usa `hide()` global y luego define regiones, ofrecer resync de la máscara con las reps de regiones.
- Etiquetas/legend/inspector: listar regions/layers con tag, tipo de representación, visibilidad y toggles rápidos para UX.
- Eventos: callbacks cuando se crean/eliminan/toggle regions/layers en JS para que Python pueda notificar a listeners del usuario.
