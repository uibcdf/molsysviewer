# Modules Overview
_Last updated: 2025-11-21_

This document describes the main logical “modules” of MolSysViewer as they
exist today. Some are implemented as separate classes/files; others are still
grouped inside `MolSysView` for simplicity.

## 1. MolSysView (Python facade)

**File:** `molsysviewer/viewer.py`

Responsibilities:
- Hold the widget (`MolSysViewerWidget`) and the underlying MolSysMT system
  (`_molsys`).
- Maintain visibility masks (`atom_mask`, `structure_mask`) and compute
  `visible_atom_indices`.
- Expose the public API for:
  - Loading (`load`, `load_pdb_string`, `load_mmcif_string`, `load_pdb_id`,
    `load_from_url`).
  - Visibility (`show`, `hide`, `isolate`).
  - Regions and layers (`new_region`, `new_layer`, `regions`, `layers`,
    `whole`).
  - Shapes (`self.shapes`).
  - Export (`write_html` con modos `standalone`/`docs` y helpers internos).
- Encapsulate Python↔JS messaging (`_send`, `_message_history`,
  `_clean_message_history`).

Internamente, `MolSysView` cumple el papel de varios módulos lógicos:

- **basic**: info, show/hide/isolate, reset de visibilidad.
- **structure**: interacción con MolSysMT (`_molsys`, selecciones, payloads).
- **shapes**: acceso a `ShapesManager`.
- **view/cam**: `reset_camera`, `get_camera_snapshot`,
  `set_camera_snapshot`, control de controles (`set_controls_visible`) y
  wrapper `Whole`.

En el futuro, algunos de estos roles podrían separarse en clases dedicadas,
pero hoy viven en `viewer.py`.

## 2. Loaders (MolSysMT y otras fuentes)

**Directorio:** `molsysviewer/loaders/`

Módulos:
- `load_molsysmt.py`  
  - Convierte cualquier `molecular_system` a `molsysmt.MolSys`, crea
    `atom_mask`, obtiene `ViewerJSON` y lo serializa a `MolSysPayload`
    (`_serialize_molsys_payload`).  
  - Envía `{"op": "load_molsys_payload", "payload": ...}` al frontend.

- `load_pdb_string.py`, `load_mmcif_string.py`  
  - Cargan PDB/mmCIF desde cadenas; crean `_molsys`, máscara de átomos y
    envían `load_structure_from_string`.

- `load_pdb_id.py`  
  - Carga sistemas por ID PDB, construye `_molsys`/máscara y envía
    `load_pdb_id` (Mol* descarga el fichero).

- `load_url.py`  
  - Carga desde URL delegando completamente en Mol*; no construye `_molsys`
    ni máscaras (no hay selecciones Python lado).

Los loaders forman el módulo lógico de **entrada de datos** y definen cómo
MolSysViewer se conecta con MolSysMT y otros orígenes.

## 3. Shapes (overlays científicos)

**Directorio:** `molsysviewer/shapes/`

Componentes:
- `ShapesManager` (`__init__.py`): fachada Python que expone métodos como
  `add_sphere`, `add_spheres`, `add_pocket_surface`, `add_channel_tube`,
  `add_anisotropy_ellipsoids`, `add_pharmacophore_features`, etc.
- Submódulos especializados:
  - `spheres.py` – esferas, sets de alpha-spheres.
  - `pocket_surfaces.py` – blobs/superficies de cavidades.
  - `pocket_blobs.py`, `channel_tubes.py`, `displacements.py`,
    `anisotropy_ellipsoids.py`, `pharmacophore.py`, etc.

Rol:
- Normalizar argumentos (longitudes, tipos, defaults).
- Construir `options` bien tipadas para los mensajes TS.
- Enviar mensajes al frontend (`{"op": "add_*", "options": {...}}`).
- Registrar/actualizar `Layer` en el registro Python (`view._layers`).

En el lado TS, estos mensajes son manejados por builders en `js/src/shapes/`
que construyen geometría Mol* (meshes, volúmenes, glyphs) y la añaden al
árbol de estado.

## 4. Regiones y capas

**Archivos:** `molsysviewer/regions.py`, `molsysviewer/layers.py`,
`molsysviewer/whole.py`, `molsysviewer/shapes/__init__.py`,
JS en `js/src/managers/handlers/state-handlers.ts`.

### 4.1 Region (Region module)
- Representa un subconjunto estructural (Mol* component) direccionado por
  `tag`.
- Propiedades: `selection`, `atom_indices`, `representation`, `repr_params`,
  `_active`.
- Métodos:
  - `set_representation(...)` (tipo simple o preset Mol* + presets de
    usuario).
  - `new_complementary_region(...)`.
  - `show()`, `hide()`, `delete()`.

### 4.2 Layer (Layer module)
- Agrupa visuales no estructurales (shapes/overlays) por `tag`.
- Mantiene `kind`, `meta` y `_active`.
- Métodos: `show()`, `hide()`, `delete()`, `set_tag()`.

### 4.3 Whole (whole module)
- Controla la representación global/base (preset o tipo simple) para toda la
  estructura.
- Mantiene flags internos (`_global_hidden`) y re-sincroniza el estado
  global con el frontend al cambiar de preset.

### 4.4 State handlers (JS)
- `state-handlers.ts` implementa el módulo de estado Mol*:
  - Índices de regiones (`regionIndex`).
  - Metadatos de capas (`layerMeta`, `tagIndex`).
  - Reps globales (`globalReprs`).
  - Visibilidad (`updateVisibility`, `show/hide_region`, `show/hide_layer`,
    `show/hide_global`).

En conjunto forman el módulo lógico de **regions/layers**, que organiza la
escena en componentes estructurales y overlays etiquetados.

## 5. Trajectory

**Archivo TS:** `js/src/managers/handlers/trajectory-handlers.ts`

Rol:
- Obtener el `Trajectory` actual desde el estado Mol*.
- Implementar:
  - `stepTrajectory(by)` (avanza/retrocede frames).
  - `setTrajectoryFrame(index)`.
  - `playTrajectory({fps, step, mode, direction})`.
  - `stopTrajectoryPlayback()`.
- Notificar a las UI (host y popup) mediante `onTrajectoryState` con:
  `frameCount`, `currentFrame`, `isPlaying`.

En Python, este módulo se refleja en los controles de UI (botones de
trayectoria y slider) y en el hecho de que `MolSysView` delega controles
de reproducción a mensajes TS.

## 6. Popup / Popout

**Archivos TS:** `js/src/managers/popup-host.ts`,
`js/src/popup/popup-logic.ts`

Módulo lógico: **popup** (ventana espejo).

Responsabilidades:
- Abrir y cerrar una ventana independiente (`PopupHostManager`).
- Inyectar el bundle JS en el popup vía Blob + `import` o usando `moduleUrl`
  cuando se exporta en modo docs.
- Crear un `MolSysViewerController` dentro del popup.
- Reproducir el `commandLog` de mensajes y snapshot de cámara inicial.
- Sincronizar estado host↔popup:
  - Ops (`molsysviewer-sync-op`).
  - Cámara (`molsysviewer-sync-camera`), solo cuando el usuario está
    interactuando.
  - Autohide de controles.
- Gestionar ciclo de vida (detección de cierre, reset de flags).

## 7. Documentación y tests

Aunque no son módulos de runtime, estos directorios forman parte del
“módulo de mantenimiento”:

- `devguide/`  
  - Diseño, arquitectura, roadmap, checkpoints y notas de implementación.

- `docs/`  
  - Documentación Sphinx, guías de usuario/desarrollador, vistas HTML
    exportadas (`_static/views/`).

- `tests/`  
  - Tests Python (unitarios + integración, incl. integración MolSysMT).

- `molsysviewer/js/tests/`  
  - Tests JS/TS:
    - Unitarios Node (`npm run test:js`).
    - E2E con Playwright (`npm run test:e2e`, ejecución manual).

Este overview debe actualizarse cuando se añadan nuevos módulos
significativos o se reorganicen componentes importantes.
