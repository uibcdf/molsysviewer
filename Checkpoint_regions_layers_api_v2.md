# MolSysViewer — Regions & Layers (Checkpoint v2)

## Estado actual
- Regiones: creación con selección o complementos; preset/representation per-region; hide/show independiente; estado `hidden` conservado al hacer `viewer.hide/show`.
- Whole: `whole` controla solo la capa base; hide antes de `show()` se respeta; `viewer.hide/show` re-oculta whole si estaba oculta.
- Layers (shapes/overlays): todos los `shapes.add_*` generan tag por defecto (`layerN`) si no se pasa, registran y devuelven `Layer`; `view.hide/show` incluye layers; `hide_layer/show_layer` funciona incluso si el mensaje llega antes de crear la shape.
- Registros públicos: `view.regions`, `view.layers` actualizados por acks; complementos funcionan; demos en `molsysviewer.demo.*`.

## Flujos verificados (UI)
1) Ocultar global antes del primer `show()` → primer `show` muestra solo regiones; global sigue oculta.
2) Regiones ocultas permanecen ocultas tras `viewer.hide(); viewer.show()`.
3) `viewer.hide/show` ahora oculta/recupera también layers (esferas, etc.).
4) `hide_layer/show_layer` funciona con tags auto o explícitos.

## Pendientes / mejoras
- Helpers Python: `get_region(tag)`, `get_layer(tag)`, `list_regions/layers` para ergonomía.
- Persistir estilo global tras `load` (reenviar último preset/representation).
- Handler JS opcional para selección string si no hay `atom_indices` (crear regiones desde frontend).
- Inspector/UX: listar regions/layers, visibilidad, tags, tipo de repr, toggles rápidos.
- Modos de coexistencia de reps: `replace` / `exclusive` para evitar solapes (regions vs global).
- Validación complementos: bloquear si falta `atom_indices` (ack pendiente) o recalcular en Python con warning claro.
- Sincronizar máscara de visibilidad con reps de regiones si el usuario usó `hide()` global antes.
- Eventos JS→Py: notificar si se crean/eliminan/tocan reps fuera del flujo Python.
- Tests: ampliar cobertura Python (complementos, errores) y JS/E2E para hide/show global/regions/layers/presets.
- Documentar más en devguide ejemplos con layers: tags auto `layerN`, retorno de `Layer` en `add_*`.

## Próximos pasos sugeridos
1) Añadir helpers de acceso (`get_region/get_layer`) y docstrings.
2) Persistencia de estilo global al recargar (`load` reaplica último preset/representation).
3) Inspector o, al menos, API para listar estados (visibles/ocultos).
4) Ampliar tests JS (unit/E2E) para layers hide/show y presets globales con tags seguros.
