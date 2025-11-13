# 🗺️ **ROADMAP para MolSysViewer**

Este roadmap describe cómo construiremos MolSysViewer desde un prototipo mínimo hasta un visor avanzado plenamente integrado con MolSysMT y TopoMT.

Cada fase está pensada para ser implementada **en orden**, sin depender de nada futuro, y dejando siempre un sistema funcional.

---

# **Fase 0 — Bootstrap del repositorio**

### 🎯 Objetivo

Crear la base técnica mínima para poder instalar el paquete y comenzar a desarrollar.

### 🔧 Tareas

* Crear repositorio `MolSysViewer`.

* Incluir:

  * `pyproject.toml` básico (build system + dependencias iniciales).
  * `molsysviewer/` con:

    * `__init__.py`
    * `_version.py`
  * `README.md` minimalista.
  * `LICENSE` (MIT).
  * `CONTRIBUTING.md` muy breve o vacío.

* Añadir:

  * `.gitignore`
  * `.pre-commit-config.yaml`
  * `.github/workflows/ci.yml`

### ✅ Resultado esperado

```python
import molsysviewer
```

funciona y el paquete se instala con:

```
pip install -e .
```

---

# **Fase 1 — Widget funcional + Mol* mínimo**

### 🎯 Objetivo

Mostrar **cualquier proteína** en Mol* dentro de un Jupyter Notebook.

### 🔧 Tareas Python

* Crear `MolSysViewerWidget` (clase DOMWidget).
* Implementar comunicación Python → JS vía `messaging.py`.
* Añadir método de usuario:

  ```python
  MolSysViewer.from_pdb_string(...)
  ```

### 🔧 Tareas TypeScript

* `index.ts`: registrar modelo/vista del widget.
* `widget.ts`: recibir mensajes y crear el `<div>` donde vivirá Mol*.
* `molstar_plugin.ts`: inicializar un viewer básico Mol*.
* Implementar mensajes esenciales:

  * `LOAD_PDB_STRING`
  * `SET_REPRESENTATION_BASIC`
  * `RESET_CAMERA`

### 📝 Ejemplo

```
from molsysviewer import MolSysViewer
MolSysViewer.from_pdb_string(pdb).show()
```

### ✅ Resultado esperado

Una estructura se visualiza correctamente en un notebook.

---

# **Fase 2 — Integración con MolSysMT (estructuras estáticas)**

### 🎯 Objetivo

Cargar sistemas de MolSysMT directamente en el visor.

### 🔧 Tareas

* Crear `molysmt_adapter.py` con funciones como:

  * `system_to_pdb_string()`
  * `system_to_mmcif_string()`
  * selección de átomos/residuos/elementos
* Integrar en la API:

  ```python
  MolSysViewer.from_molysmt(system)
  ```
* Añadir funcionalidades básicas:

  * cartoon, sticks, surface
  * selección de componentes

### 🧪 Ejemplo Notebook

`02_molysmt_integration.ipynb`

### ✅ Resultado esperado

El usuario puede visualizar cualquier sistema cargado con MolSysMT.

---

# **Fase 3 — Trayectorias (sin overlays dinámicos aún)**

### 🎯 Objetivo

Reproducir trayectorias de MD en el visor.

### 🔧 Tareas Python

* `TrajectoryData` en `data_models.py`.
* Método:

  ```python
  viewer.add_trajectory(traj)
  viewer.frame = 10
  viewer.play()
  ```

### 🔧 Tareas TypeScript

* Mol* `CoordinateTrajectory` o equivalente.
* Mensajes:

  * `LOAD_TRAJECTORY_METADATA`
  * `SET_FRAME`
  * opcional: `PLAY`, `PAUSE`

### 🧪 Ejemplo Notebook

`01_basic_viewer.ipynb` + trayectorias.

### ✅ Resultado esperado

Una trayectoria puede reproducirse con un slider o animación.

---

# **Fase 4 — Integración con TopoMT: cavidades**

### 🎯 Objetivo

Visualizar cavidades TopoMT como:

* nubes de puntos,
* mallas cerradas,
* mallas abiertas (más adelante).

### 🔧 Tareas

* Implementar `topomt_adapter.py`

  * conversión `Cavity` → `CavityCloud` / `CavityMesh`
* Representaciones Python:

  * `show_cavity_cloud(...)`
  * `show_cavity_mesh(...)`
* Representaciones TypeScript:

  * `cavities-repr.ts`

    * punto-impóstor (esferas),
    * superficies triangulares.

### 🧪 Ejemplo Notebook

`03_topomt_cavities.ipynb`

### ✅ Resultado esperado

Cualquier cavidad detectada en TopoMT puede visualizarse.

---

# **Fase 5 — Overlays dinámicos (H-bonds y similares)**

### 🎯 Objetivo

Visualizar elementos que cambian por frame.

### 🔧 Tareas Python

* `HbondSeries` en `data_models.py`
* Representación de usuario:

  ```python
  viewer.show_hbonds(hbonds_by_frame)
  ```

### 🔧 Tareas TypeScript

* `hbonds-repr.ts`

  * líneas/cilindros actualizables en cada frame
* Mensajes:

  * `SET_DYNAMIC_LINES`
    (o protocolo de dataset completo + actualización automática según `frame`)

### 🧪 Ejemplo Notebook

`04_dynamic_overlays.ipynb`

### ✅ Resultado esperado

H-bonds aparecen y desaparecen en sincronía con la trayectoria.

---

# **Fase 6 — Mallas abiertas, secciones y clipping**

### 🎯 Objetivo

Funciones avanzadas para inspección de cavidades.

### 🔧 Tareas

* Añadir soporte para:

  * mallas abiertas de `Mouth`, `BaseRim`, `Interface`
  * clipping planes configurables
  * “cutaways” (secciones internas)

### 🔧 TypeScript

* Ampliar `cavities-repr.ts`
* Añadir hooks para clipping y cortes.

### 🧪 Ejemplo Notebook

Exploración visual detallada de cavidades profundas.

### ✅ Resultado esperado

Exploración intuitiva de interiores de cavidades.

---

# **Fase 7 — Rendimiento, UX y documentación**

### 🎯 Objetivo

Terminar de pulir el visor como herramienta sólida para usuarios y desarrolladores.

### 🔧 Tareas

* Optimización:

  * transmisión binaria opcional,
  * reducción del tamaño de mensajes,
  * manejo de trayectorias largas y muchas cavidades.
* Mejoras de UX:

  * panel interactivo en notebook (ipywidgets)
  * presets
* Documentación:

  * arquitectura detallada
  * guía de usuario
  * guía para desarrolladores
* Ejemplos reales de investigación.

### ✅ Resultado esperado

MolSysViewer listo para uso habitual y contribuciones externas.

---

# **Fase opcional futura — Versión web independiente**

🎯 Reutilizar el núcleo Mol* + representaciones para crear una web standalone.

Esto es otro proyecto, pero:

* **MolSysViewer ya lo prepara desde el diseño**,
* separando “núcleo de visualización” de “pegamento Jupyter”.


