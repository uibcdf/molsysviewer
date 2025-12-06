# MolSysViewer — Regions & Layers (Developer Notes)

## Naming & Concepts
- **Region**: subconjunto estructural (Mol* component) identificado por `tag` (user o auto). Guarda selección y `atom_indices`.
- **Layer**: grupo de visuales no estructurales (shapes/overlays). Identificado por `tag`.
- Auto-tags si no se pasa uno: `region1`, `layer1`, ...

## API Python (esbozo)
- `view.new_region(selection, tag=None, representation=None, **repr_params) -> Region`
- `view.new_layer(kind=None, tag=None, **meta) -> Layer`
- Registros públicos: `view.regions` / `view.layers` (acceso: `view.regions["set1"].hide()`).
- `Region`: `set_representation(...)`, `hide()/show()`, `delete()`, complementos (`new_complementary_region()`), selección modificable en futuro.
- `Layer`: `hide()/show()`, `delete()`, `set_tag()/merge()` opcional.
- Global: `view.global_view` (`set_representation`, `hide()/show()`), no eliminable ni retaggable.
- Complementos: `new_region(..., complement_of_regions=["tagA", ...] | "all")` calcula complementos en Python, requiere sistema cargado y `atom_indices` conocidos de esas regiones.

## Responsabilidades JS
- Fuente de verdad de refs Mol*: regiones (`tag -> componentRef, reprRefs[], atomIndices[], selection, hidden`), layers (`tag -> refs, kind/meta`), global (`globalReprs`).
- Handlers: create/set/show/hide/delete región; idem layers; set/hide/show global; clear/reset/load limpia registros y notifica a Python.
- Acks a Python: `region_ack` (incluye `atom_indices`, selection), `layer_ack`, `registry_cleared`.
- Shapes: se taggean y registran como layers por `tagIndex`.

## Visibilidad (global vs regiones vs viewer)
- `region.hide()/show()`: sólo esa región; el estado `hidden` se recuerda, `viewer.show()` no las reenciende.
- `global_view.hide()/show()`: sólo representación base/global (auto/preset/cartoon de `load`); no toca regiones. Si se invoca antes del primer `show()`, se memoriza y aplica al cargar la estructura.
- `viewer.hide()/show()` con `selection="all"`: ajusta máscara de átomos y envía `hide_global/show_global target=all`; respeta regiones ocultas y re-oculta global si estaba marcada como oculta.

### Flujos de referencia
1) Ocultar global antes de mostrar
```python
view = viewer.demo.tctim
view.global_view.hide()
view.show()  # sólo regiones creadas; global permanece oculta
```
2) Ocultar región y mantenerla tras hide/show general
```python
view = viewer.demo.tctim
r1 = view.new_region("chain_id == 'A'", representation="sticks")
r2 = view.new_region("chain_id == 'B'", representation="sticks")
r2.hide()
view.hide(); view.show()  # r1 visible, r2 sigue oculta; global según flag
```
3) Ocultar todo y reactivar sólo lo visible
```python
view.hide()  # oculta global + regiones + máscara de átomos
view.show()  # regiones ocultas siguen ocultas; global según su estado
```

## Presets globales y tags: precaución
- El filtro que separa “global” de “regiones” asume que las reps base/global no usan tags de región (o usan tag `global`/sin tag).  
- Si un preset global personalizado crea representaciones con un `tag` idéntico a una región, se considerarán “región” y pueden ser excluidas de las operaciones de global (p.ej., `global_view.hide()` podría no ocultarlas).  
- Recomendaciones:
  1. Para presets globales, no asignar tags de regiones; usar `tag="global"` o sin tag.
  2. Si se necesita aplicar un preset a una región concreta, hacerlo vía `region.set_representation(preset=...)`, no vía `global_view`.
  3. Si se hereda de un preset Mol* y se añaden reglas, evitar tags que colisionen con regiones; ejemplo seguro:
     ```python
     view.global_view.set_representation(
         preset="auto",
         params={"ignoreHydrogens": True},
     )
     # Reglas por selección, sin tag explícito de región:
     # [{"selection": "ligand", "representation": "ball-and-stick"}]
     ```

## Estado actual (branch)
- API Python funcional (regiones, layers, global_view, complementos, presets/aliases).
- JS controller con registros, hide/show independentes, cola de ops pendientes (global/regions) antes de `show()`, global auto `auto/cartoon`.
- Demos para tests/manual: `demo.dialanine`, `demo.pentalanine`, `demo.tctim`, `demo.chicken_villin_HP35`.

## Pendientes / Ideas
- Helpers `get_region/get_layer/list_*`; inspector UI de regions/layers y visibilidad.
- Persistir estilo global tras `load`.
- Handler JS para selection string si no hay `atom_indices`.
- Eventos JS→Py si se modifican reps fuera del flujo Python.
- Modos de coexistencia de reps: `replace` / `exclusive` para evitar solapes.
- Validación de complementos cuando falten `atom_indices` (acks).
- Sincronizar máscara de visibilidad con regiones si el usuario usó `hide()` global primero.
