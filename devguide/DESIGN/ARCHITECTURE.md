# Architecture
_Last updated: 2025-11-21_

This document complements `DESIGN/OVERVIEW.md` with a more concrete view of
the current architecture: how the Python and TypeScript layers are wired
together, what data flows exist, and which parts are implemented vs. aspirational.

## 1. High-level layers (recap)

MolSysViewer is split into:

- **Python layer (`molsysviewer/`)**
  - `MolSysView` facade and widget wrapper.
  - Loaders for MolSysMT/PDB/mmCIF/URL.
  - Regions/layers/GlobalView and shapes APIs.
  - HTML export helpers for docs.

- **TypeScript/Mol\* layer (`molsysviewer/js/src/`)**
  - Anywidget entry (`index.ts`).
  - `MolSysViewerController` and handlers (`loader`, `scene`, `state`,
    `trajectory`).
  - Shape builders in `shapes/`.
  - Popup host + popup implementation.

`DESIGN/OVERVIEW.md` describe un modelo modular (“basic”, “structure”,
“shapes”, “cam”, “hbonds”, “topology”). En la implementación actual, esos
roles están parcialmente fusionados en `MolSysView` y los submódulos
mencionados arriba.

## 2. Python ↔ JS message protocol

### 2.1 Python → JS

Todas las acciones visuales se envían como diccionarios JSON-like con:

- `op`: string que identifica la operación.
- `options` o campos adicionales según la operación.

Ejemplos reales:

- Cargar payload MolSysMT:
  ```python
  view._send({
      "op": "load_molsys_payload",
      "payload": payload,
      "label": label,
  })
  ```
- Actualizar visibilidad:
  ```python
  view._send({
      "op": "update_visibility",
      "options": {"visible_atom_indices": visible_indices},
  })
  ```
- Shapes:
  ```python
  self._view._send({
      "op": "add_sphere",
      "options": {...},
  })
  ```
- Regiones/capas/global:
  - `create_region`, `set_region_representation`,
    `show_region` / `hide_region` / `delete_region`
  - `create_layer`, `show_layer` / `hide_layer` / `delete_layer`,
    `set_layer_tag`
  - `set_global_representation`, `show_global`, `hide_global`

El tipo TS `ViewerMessage` (`js/src/messages/viewer-messages.ts`) enumera
estas variantes y sirve como contrato de tipos.

### 2.2 JS → Python

El widget recibe mensajes de vuelta mediante `widget.on_msg`. Eventos
actuales:

- `"ready"` – el frontend está inicializado; `MolSysView` vacía la cola
  `_pending_messages` en el widget.
- `"region_ack"` – el handler JS confirma creación de región y devuelve
  `atom_indices` y `selection` definitivos.
- `"region_deleted"` – una región ha sido eliminada.
- `"layer_ack"` – confirmación de creación/actualización de layer.
- `"layer_deleted"` – capa eliminada.
- `"registry_cleared"` – se ha hecho `clear_all`; Python debe resetear
  registros y contadores.
- `"js_log"` – logs de debug desde el bundle cuando `debug_js=True`.

Estos eventos mantienen sincronizados los espejos Python (`view.regions`,
`view.layers`) con el árbol de estado de Mol\*.

## 3. Data path: MolSysMT → Mol\*

1. El usuario llama a `MolSysView.load(molecular_system, ...)`.
2. `load` delega en `loaders.load_from_molsysmt`:
   - Convierte a `molsysmt.MolSys`.
   - Guarda `_molsys`, `molecular_system`, `selection`, `structure_indices`.
   - Crea `atom_mask` todo True.
   - Obtiene `ViewerJSON` y lo serializa a `MolSysPayload`:
     - `atoms`: arrays paralelos (id, nombre, residuo, cadena, elemento,
       carga).
     - `structures`: lista de snapshots con `coordinates` en Å, `box`
       opcional, `time` opcional.
     - `bonds` opcional: `indexA/indexB` (+ `order`).
3. `MolSysView` envía `{"op": "load_molsys_payload", "payload": ...}`.
4. En TS, `LoaderHandlers` llama a
   `loadStructureFromMolSysPayload(plugin, payload, ...)`:
   - Crea tabla `atom_site` (`BasicSchema`) y `Topology`.
   - Construye `Coordinates` a partir de las estructuras.
   - Genera `Trajectory` Mol* con `Model.trajectoryFromTopologyAndCoordinates`.
   - Inserta un nodo de trayectoria en el árbol de estado con el transformador
     `InsertMolSysTrajectory`.
   - Aplica preset Mol* por defecto (`"default"`/`"auto"`).
5. `LoaderHandlers` actualiza `loadedStructure` y llama a
   `captureCurrentStructure`, que notifica a `StateHandlers` y
   `TrajectoryHandlers` que la estructura ya está lista.

Este camino evita conversiones PDB intermedias cuando se usa MolSysMT.

## 4. Visibilidad y máscaras

### 4.1 Python

- `MolSysView` mantiene una máscara booleana `atom_mask` de longitud `n_atoms`.
- `hide(selection)`:
  - Si `selection` es `"all"` → pone toda la máscara a `False`, envía
    `hide_global target="all"` para ocultar todas las reps.
  - Si no, usa `molsysmt.select` para obtener índices y los marca como
    `False`.
  - Llama a `_update_visibility_in_frontend()`.
- `show(selection, structure_indices, force=False)`:
  - Si `selection` y `structure_indices` son `"all"` → rellena la máscara con
    `True`, envía `show_global target="all"` y luego respeta el flag
    `_global_hidden` (`hide_global`/`show_global` para la vista base).
  - Si no, activa sólo los índices seleccionados.
  - Si es la primera llamada (o `force=True`), devuelve el widget para
    Jupyter; en llamadas posteriores sin `force` no devuelve nada.

La propiedad `visible_atom_indices` se calcula como `np.nonzero(atom_mask)[0].tolist()`
y se envía en `update_visibility`.

### 4.2 JS

- `StateHandlers.updateVisibility`:
  - Si no hay estructura aún, guarda `pendingVisibility`.
  - Si hay estructura y componentes:
    - Limpia transparencia (`clearStructureTransparency`).
    - Construye un `StructureSelection` que recoge los átomos a ocultar
      (complemento de la lista de visibles).
    - Aplica transparencias/visibilidad a reps globales y de regiones
      usando `setSubtreeVisibility` y helpers Mol*.

Este diseño mantiene el “source of truth” de visibilidad en Python, pero
usa la infraestructura de representaciones de Mol\* para el renderizado.

## 5. Regions & Layers

### 5.1 Python (API)

- `MolSysView.new_region(...)`:
  - Acepta selección MolSysMT o `atom_indices` explícitos.
  - Soporta `complement_of_regions` (`["tagA", ...]` o `"all"`).
  - Crea un objeto `Region` y lo registra en `self._regions[tag]`.
  - Envía `create_region` con selección, índices, representación y params.

- `Region.set_representation(...)`:
  - Normaliza tipo/preset y presets de usuario.
  - Envía `set_region_representation`.

- `Region.show/hide/delete`:
  - Envían `show_region`, `hide_region`, `delete_region` y actualizan el
    registro Python a partir de los eventos JS.

- `MolSysView.new_layer(...)`:
  - Crea un `Layer`, lo registra y envía `create_layer`.

- `Layer.show/hide/delete/set_tag`:
  - Envía `show_layer`, `hide_layer`, `delete_layer`, `set_layer_tag`
    y mantiene sincronizado el registro.

- `GlobalView.set_representation(...)`:
  - Resuelve presets de usuario en Python (vía MolSysMT) y envía
    `set_global_representation` + payload de user preset.

### 5.2 JS (estado Mol\*)

- `StateHandlers` mantiene:
  - `regionIndex`: `tag -> {component, representations[], atomIndices[], selection, hidden}`.
  - `layerMeta`: `tag -> {kind, meta}` y `tagIndex`: `tag -> StateObjectRef set`
    para shapes.
  - `globalReprs`: reps globales asociadas al root `Structure`.
  - Flags de visibilidad y operaciones globales pendientes cuando aún no hay
    estructura cargada.

Cuando recibe mensajes:

- `create_region` → construye un `StructureSelection` a partir de los índices,
  crea `StructureComponent`, añade reps y guarda refs.
- `set_region_representation` → elimina reps previas y aplica preset global,
  user preset o tipo simple.
- `show/hide_region` → usa `setSubtreeVisibility` sobre las reps de la región.
- `create_layer` → almacena metadatos y notifica a Python.
- `show/hide_layer` → ajusta visibilidad de todos los refs asociados al tag.
- `set_global_representation` → reconstruye las reps globales (y reglas de
  presets de usuario) y las añade a `globalReprs`.
- `show/hide_global` → muestra/oculta reps globales y, opcionalmente, todas
  las demás cuando `target="all"`.

`clear_all` limpia regiones, capas y reps globales, elimina la estructura
del árbol Mol* (a través de `MolSysViewerController.removeLoadedStructure()`)
y emite `registry_cleared` hacia Python.

## 6. Popup architecture (host ↔ popup)

- **Host (notebook)**:
  - `PopupHostManager` abre la ventana, construye un Blob con el código
    fuente de `viewer.js` y lo `import`a en el contexto del popup.
  - Llama a `bootPopup(module)` dentro del popup.
  - Mantiene un `commandLog` (lista de mensajes Python→JS) para poder
    reconstruir el estado en el popup.
  - Usa `postMessage` para:
    - Enviar `molsysviewer-initial-sync` (mensajes + snapshot de cámara +
      estado de spin/swing/dark/autohide).
    - Enviar `molsysviewer-sync-op` por cada nuevo mensaje Python→JS.
    - Enviar `molsysviewer-sync-camera` cuando la cámara del host cambia
      mientras el usuario interactúa.

- **Popup**:
  - `bootPopup` crea su propio `MolSysViewerController` apuntando al DOM
    del popup.
  - Espera a que `canvas3d` exista y se suscribe a `didDraw` para enviar
    snapshots de cámara al host solo cuando el usuario interactúa en el
    popup.
  - Escucha `postMessage` para:
    - `molsysviewer-initial-sync` (reproducir `commandLog`, snapshot,
      estado de spin/swing/dark, autohide).
    - `molsysviewer-sync-op` (aplicar operaciones).
    - `molsysviewer-sync-camera` (aplicar cámara host→popup si el usuario
      no está “peleando” por la cámara).

Este diseño mantiene el popup como un “espejo vivo” del host, con sync de
estado explícito y evitando bucles de cámara.

## 7. Qué partes siguen siendo aspiracionales

`DESIGN/OVERVIEW.md` menciona módulos adicionales (hbonds, topology, motores
alternativos) y una API `structure.get_* / show_*` más rica. A día de hoy:

- El núcleo de:
  - carga MolSysMT,
  - shapes científicos básicos (esferas, pockets, tubos, farmacóforo),
  - regions/layers/global,
  - popup,
  - trayectorias

está implementado.

- Siguen siendo futuros:
  - módulo de `hbonds` dedicado (`get_hbonds/show_hbonds`).
  - módulo `topology` con APIs `get_bonds/show_bonds` de alto nivel.
  - APIs numéricas avanzadas (`get_distances/get_angles/...`) dentro de
    MolSysViewer (hoy se espera que el usuario recurra directamente a
    MolSysMT para esos cálculos).
  - soporte multi-motor (`engine="molstar"/"numpy"/"numba"/"cupy"`).

Este documento debe revisarse cuando alguno de estos módulos pase de
“diseño” a implementación real.
