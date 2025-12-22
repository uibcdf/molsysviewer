# MolSysViewer — Repository Structure
_Last updated: 2025-11-21_

This document describes how the MolSysViewer repository is organized as of the
current development cycle. It is intended as a quick map for contributors.

## Top-level layout (repository root)

- `pyproject.toml`  
  - Python packaging configuration (build-system, project metadata, optional
    `dev` extras, versioningit).
  - Declares `molsysviewer` as the main package and includes data files
    (`viewer.js`, `.map`, H5MSM demos).

- `molsysviewer/`  
  - Python package: widget wrapper, public API, loaders, shapes and integration
    utilities.

- `molsysviewer/js/`  
  - TypeScript + Mol* sources and Node toolchain.  
  - Contains `src/`, `package.json`, `tsconfig.json` and tests under
    `tests/`. Includes `scripts/` helpers for tooling (e.g. syncing the
    JS package version with the Python version).

- `devguide/`  
  - Internal design, structure, planning and history documents.  
  - This is where architecture, roadmap and checkpoints live.

- `devtools/`  
  - Conda recipe and environment definitions:
    - `conda-build/` (recipe + `build.sh`)
    - `conda-envs/` (development/build/docs envs).

- `docs/`  
  - Sphinx documentation (user + developer), MyST notebooks and static HTML
    exports of the viewer (docs builds copy a runtime bundle to
    `_static/molsysviewer-runtime.js`).

- `tests/`  
  - Python test suite (unit + integration).

- `sandbox/`  
  - Notebooks y scripts de exploración manual (no se usan en CI).

- `.github/`  
  - CI workflows, plantillas de PR y guía de contribución.

- `Checkpoint_*.md`, `ideas*.md`  
  - Documentos de reflexión y checkpoints puntuales (popup, regions/layers,
    APIs).

## Python package (`molsysviewer/`)

Estructura principal:

- `__init__.py`  
  - Exporta `MolSysView`, `load`, `demo` y `__version__`.

- `viewer.py`  
  - Clase `MolSysView`:  
    - Posee el widget (`MolSysViewerWidget`), el sistema MolSysMT (`_molsys`)
      y máscaras de visibilidad (`atom_mask`, `structure_mask`).
    - API de alto nivel: `load`, `load_pdb_string`, `load_mmcif_string`,
      `load_pdb_id`, `load_from_url`, `show`, `hide`, `isolate`,
      `new_region`, `new_layer`, `clear_decorations`, `reset_camera`,
      `get_camera_snapshot`, `set_camera_snapshot`, `reset_viewer`,
      `write_html` (modos `standalone`/`docs`).
    - Registro público de `regions` y `layers`, wrapper `whole`,
      gestor de shapes (`self.shapes`).
    - Cola/historial de mensajes para el frontend y para exportar HTML
      (`_send`, `_message_history`, `_clean_message_history`).

- `widget.py`  
  - Clase `MolSysViewerWidget(anywidget.AnyWidget)`.  
  - Carga `viewer.js` como `_esm` y expone traits sincronizados:
    `popup_js_source`, `initial_messages`, `show_controls`,
    `autohide_controls`, `enable_popout`, `debug_js`, posiciones de controles,
    etc.

- `load.py`  
  - Función de conveniencia `load(molecular_system, ...)` que instancia
    (o reutiliza) un `MolSysView` y llama a `MolSysView.load`.

- `loaders/`  
  - Integración con MolSysMT y otros orígenes:
    - `load_molsysmt.py` – conversión a `molsysmt.MolSys`, generación de
      `MolSysPayload` (ViewerJSON→payload) y envío de `load_molsys_payload`.
    - `load_pdb_string.py`, `load_mmcif_string.py` – carga PDB/mmCIF como
      cadenas, construye `_molsys` y envía `load_structure_from_string`.
    - `load_pdb_id.py` – carga por ID PDB (MolSysMT + descarga en Mol*).
    - `load_url.py` – delega parseo a Mol* (sin `_molsys` ni máscara).

- `shapes/`  
  - API Python para overlays científicos:
    - `__init__.py` – `ShapesManager` y exports de submódulos.
    - `spheres.py`, `pocket_surfaces.py`, `pocket_blobs.py`,
      `channel_tubes.py`, `displacements.py`, `anisotropy_ellipsoids.py`,
      `pharmacophore.py`, etc.
  - Normalizan argumentos y envían mensajes (`op: add_*`) al frontend;
    mantienen `Layer` en el registro Python.

- `regions.py`, `layers.py`, `whole.py`  
  - `Region` – wrapper de componentes Mol* por `tag` (selección, índices,
    representación, complementos).
  - `Layer` – capa de visuales no estructurales, con `hide/show/delete` y
    `set_tag`.
  - `Whole` – control de representación/preset global y visibilidad
    de la capa base.

- `_private/`  
  - Utilidades internas (`variables.py`) para `is_all`, checks de coordenadas,
    etc.

- `config/`  
  - `user_presets.py` – presets de usuario (reglas por selección) que se
    resuelven vía MolSysMT.

- `thirds/`  
  - Integraciones auxiliares (por ahora, helper de Jupyter para embeber HTML).

- `data/h5msm/`  
  - Sistemas demo (`dialanine`, `pentalanine`, `tctim`, `chicken_villin`).

## TypeScript/Mol* (`molsysviewer/js/`)

Estructura simplificada:

- `src/index.ts`  
  - Punto de entrada anywidget (`render`).  
  - Crea el contenedor DOM, inicializa `MolSysViewerController`,
    construye los controles (`buildControls`) y gestiona el popup host.
  - Maneja mensajes Python→JS (`msg:custom`) y mensajes host↔popup
    (`postMessage`); exporta `bootDocsView` para exports docs-light.

- `src/managers/viewer-controller.ts`  
  - Clase `MolSysViewerController`:
    - Posee `PluginContext` de Mol*.
    - Instancia handlers: `loader`, `scene`, `state`, `trajectory`,
      `shapes` (cuando aplique).
    - Despacha `ViewerMessage.op` a los handlers.
    - Expone helpers de cámara, fullscreen, background, spin/swing y
      control de trayectoria.

- `src/messages/viewer-messages.ts`  
  - Definición tipada de todos los mensajes `ViewerMessage` (`op` +
    payload) compartidos con Python.

- `src/plugin/structure.ts`  
  - Funciones para cargar estructuras en Mol* desde:
    - PDB/mmCIF (string/URL).
    - Payload `MolSysPayload` (atoms + structures + bonds + meta).
  - Construye `Topology`, `Coordinates`, `Trajectory` y `Structure`
    usando APIs Mol*.

- `src/managers/handlers/*.ts`  
  - `loader-handlers.ts` – orquesta `load_*` y guarda `LoadedStructure`.
  - `scene-handlers.ts` – cámara, fullscreen, fondo, limpieza de escena.
  - `state-handlers.ts` – registros de regiones/layers, reps globales,
    visibilidad, clear/reset.
  - `trajectory-handlers.ts` – stepping, reproducción y estado de
    trayectorias.

- `src/shapes/`  
  - Builders de geometría avanzados (superficies de pocket, blobs, tubos,
    etc.) usando internals de Mol* (Gaussian density, marching cubes,
    shape representations).

- `src/ui/controls.ts`  
  - Overlay de controles (Reset/Full/Bg/Spin/Swing/Pop) y barra de
    trayectoria (slider, step, fps, play/pause).

- `src/popup/popup-logic.ts`  
  - Lógica que corre dentro del popup:
    - Crea un `MolSysViewerController` independiente.
    - Reproduce el `commandLog` y snapshot de cámara inicial.
    - Sincroniza cámara host↔popup de forma dependiente de la interacción
      del usuario.

- `tests/unit/`, `tests/e2e/`  
  - Unitarios JS/TS (Node + esbuild).  
  - E2E con Playwright + Chromium (manual, requiere WebGL).

## Otros directorios clave

- `devguide/` – documentos internos (diseño, estructura, roadmap,
  checkpoints).  
- `docs/` – documentación Sphinx (usuario/desarrollador), incluye vistas
  HTML exportadas.  
- `tests/` – tests Python (unitarios + integración, incluyendo flujo
  MolSysMT).  
- `sandbox/` – notebooks de experimentación (no forman parte de la
  batería oficial).

Este esquema debe mantenerse actualizado cuando se introduzcan nuevos
submódulos importantes o se reorganicen directorios.
