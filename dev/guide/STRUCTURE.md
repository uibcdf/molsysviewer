
## Nombre y propósito

* **Nombre del proyecto:** `MolSysViewer`
* **Paquete Python:** `molsysviewer`
* **Objetivo:** visor interactivo en Jupyter basado en **Mol*** para:

  * estructuras de **MolSysMT**,
  * entidades de **TopoMT** (cavities, mouths, etc.),
  * trayectorias de dinámica molecular,
  * overlays dinámicos (puentes de hidrógeno, etc.).

Piensa en MolSysViewer como el “front-end visual estándar” del ecosistema MolSysMT/TopoMT.

La librería es programadada en Python 3.10+ y TypeScript, usando **ipywidgets** para la integración con Jupyter y el plugin de **Mol*** para la visualización 3D.
---

## Estructura lógica del repositorio

### 1. Raíz del proyecto

En la raíz del repo `MolSysViewer/` tendremos:

* `pyproject.toml`
  Configuración del paquete (nombre `molsysviewer`, dependencias, etc.).

* `README.md`
  Descripción general, instalación rápida, ejemplo mínimo.

* `LICENSE`
  Probablemente MIT, en línea con MolSysMT/TopoMT.

* `CONTRIBUTING.md` (más adelante)
  Guía para colaboraciones (issues, PRs, estilo de código, etc.).

* Ficheros de utilidades:

  * `.gitignore`
  * `.pre-commit-config.yaml` (formateo, linters)
  * `.github/workflows/` para CI (tests, docs, etc.).

---

### 2. Paquete Python: `molsysviewer/`

Este es el **núcleo Python** que usarás en los notebooks.

#### 2.1. Ficheros de núcleo

* `molsysviewer/__init__.py`
  Exporta la API de alto nivel, por ejemplo:

  ```python
  from .viewer import MolSysViewer
  ```

* `molsysviewer/_version.py`
  Versión del paquete.

* `molsysviewer/viewer.py`
  **API de alto nivel para el usuario**.
  Aquí vive la clase principal:

  ```python
  class MolSysViewer:
      @classmethod
      def from_molysmt(cls, system): ...
      @classmethod
      def from_pdb_string(cls, pdb): ...
      def add_trajectory(self, traj): ...
      def show_cavity(self, cavity, mode="cloud", opacity=0.4): ...
      def show_hbonds(self, hbonds_by_frame): ...
      # y otros helpers de “usuario final”
  ```

* `molsysviewer/widget.py`
  El **ipywidget** real:

  ```python
  from ipywidgets import DOMWidget
  from traitlets import Unicode, Dict, Int

  class MolSysViewerWidget(DOMWidget):
      _model_name = Unicode("MolSysViewerModel").tag(sync=True)
      _view_name = Unicode("MolSysViewerView").tag(sync=True)
      _model_module = Unicode("molsysviewer").tag(sync=True)
      _view_module = Unicode("molsysviewer").tag(sync=True)

      state = Dict().tag(sync=True)
      frame = Int(0).tag(sync=True)
  ```

  Este objeto es el que se muestra en el notebook (el canvas de Mol* vive en el front-end, pero está ligado a esta clase).

* `molsysviewer/messaging.py`
  Funciones auxiliares para enviar comandos:

  ```python
  def send_command(widget, op: str, payload: dict) -> None:
      widget.send({"op": op, "payload": payload})
  ```

  con nombres de operaciones tipo:

  * `"LOAD_PDB_STRING"`,
  * `"SET_REPRESENTATION"`,
  * `"SET_FRAME"`,
  * `"SET_CAVITY_POINTCLOUD"`,
  * `"SET_CAVITY_MESH"`,
  * `"SET_DYNAMIC_LINES"`, etc.

* `molsysviewer/data_models.py`
  Modelos de datos (probablemente `dataclasses`) para empaquetar cosas antes de mandarlas al front-end:

  * `CavityCloud` (positions, radii, color, opacity),
  * `CavityMesh` (vertices, faces, color, opacity),
  * `HbondSeries` (segmentos por frame),
  * `TrajectoryData` (frames, topología),
  * parámetros visuales (colores, estilos…).

---

#### 2.2. Integración con otras librerías

* `molsysviewer/adapters/`

  * `molysmt_adapter.py`
    Funciones que toman objetos de MolSysMT y los transforman en:

    * `TrajectoryData`,
    * estructuras en formato PDB/mmCIF,
    * selecciones lógicas, etc.

  * `topomt_adapter.py`
    Para entidades de TopoMT:

    * `Topography`, `Cavity`, `Mouth`, `BaseRim`, etc.
      → se convierten en `CavityCloud`, `CavityMesh`, etc.

  La idea: **el visor no “sabe” de MolSysMT/TopoMT directamente**; habla con modelos genéricos. Los adapters son la capa que traduce.

---

#### 2.3. Lado Python de las representaciones

* `molsysviewer/representations/`

  Aquí pones helpers que empaquetan “cosas científicas” en comandos de visualización.

  * `cavities.py`

    ```python
    def show_cavity_cloud(viewer, cavity, **kwargs): ...
    def show_cavity_mesh(viewer, cavity, **kwargs): ...
    ```

  * `hbonds.py`

    ```python
    def show_hbonds(viewer, hbonds_by_frame, **kwargs): ...
    ```

  * `trajectories.py`

    ```python
    def add_trajectory(viewer, traj, **kwargs): ...
    ```

  * `shapes.py`

    ```python
    def add_sphere_cloud(viewer, positions, radii, **kwargs): ...
    def add_lines(viewer, segments, **kwargs): ...
    ```

  El fichero `viewer.py` usa estas funciones para ofrecer una API simple.

---

#### 2.4. Integración con Jupyter

* `molsysviewer/_jupyter/`
  Aquí irá lo necesario para registrar la extensión como widget (labextension/nbextension), aunque muchos detalles los genera el tooling de ipywidgets. Es básicamente “pegamento” para que Jupyter reconozca el widget.

---

### 3. Front-end TypeScript: `js/`

Esta carpeta es el mundo JS/TS:

* `js/package.json`, `js/tsconfig.json`, `js/webpack.config.js` (o equivalente)
  Configuración del paquete y compilación.

* `js/src/index.ts`
  Punto de entrada que registra el widget para Jupyter (modelo y vista).

* `js/src/widget.ts`
  Implementación del modelo y vista del lado del navegador:

  * crea el contenedor HTML,
  * inicializa Mol*,
  * escucha mensajes `this.model.on("msg:custom", ...)`,
  * delega en el plugin de Mol*.

* `js/src/molstar_plugin.ts`
  Código que realmente:

  * crea y configura el viewer Mol*,
  * carga estructuras/trajectorias,
  * define métodos como `updateCavityCloud`, `updateCavityMesh`, `updateDynamicLines`, etc.

* `js/src/representations/`
  Módulos TS con representaciones personalizadas en Mol*:

  * `cavities-repr.ts`: nubes de puntos y mallas de cavidades,
  * `hbonds-repr.ts`: líneas/cilindros dinámicos para H-bonds,
  * `pointcloud-repr.ts`: nubes genéricas de puntos (reusable).

* `js/src/utils/`

  * `messaging.ts`: helpers para manejar los comandos entrantes.
  * `molstar-helpers.ts`: funciones para construir geometría, aplicar colores, temas, etc.

---

### 4. Documentación: `docs/`

Más adelante, cuando el proyecto avance:

* `docs/index.md` – portada de la doc.
* `docs/architecture.md` – cómo se conectan Python, ipywidgets y Mol*.
* `docs/user-guide.md` – uso básico para gente que solo quiere visualizar sus sistemas.
* `docs/dev-guide.md` – cómo extender MolSysViewer con nuevas representaciones.
* `docs/api-reference.md` – detalle de la API Python.

---

### 5. Ejemplos: `examples/`

Notebooks demostrativos, por ejemplo:

* `01_basic_viewer.ipynb` – cargar un PDB en bruto.
* `02_molysmt_integration.ipynb` – usar MolSysMT como fuente de sistemas.
* `03_topomt_cavities.ipynb` – mostrar cavidades, bocas, etc.
* `04_dynamic_overlays.ipynb` – trayectorias + H-bonds dinámicos.

---

### 6. Tests: `tests/`

* Tests Python:

  * que `MolSysViewer` se instancia,
  * que los adapters generan datos coherentes,
  * que el `messaging` crea comandos con la estructura correcta.

* Más adelante podrían añadirse tests (aunque sean smoke tests) para el lado JS.

---

## Mensaje clave para recordar

* **MolSysViewer** tiene dos almas:

  * El **lado Python** (molsysviewer): integra MolSysMT/TopoMT, define la API de usuario y empaqueta datos.
  * El **lado TypeScript** (js/): inicializa Mol*, define representaciones visuales y responde a mensajes.

* La estructura está pensada para:

  * crecer en funcionalidades (más representaciones, más overlays),
  * no casarte solo con MolSysMT (los adapters aíslan esa dependencia),
  * y, si un día quieres, poder reutilizar el “núcleo Mol* + representaciones” en una futura web.


