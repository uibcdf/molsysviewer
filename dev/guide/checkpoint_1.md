## 1. Qué hemos simplificado (a propósito) y que queda marcado para revisión futura

Aquí están las **concesiones/simplificaciones** que hemos hecho para tener algo funcional lo antes posible:

1. **Arquitectura de widgets (lado Python) muy mínima**

   * Solo tenemos **un** widget base: `MolSysViewerWidget(DOMWidget)`.
   * El widget expone:

     * `_model_name = "MolSysViewerModel"`
     * `_view_name = "MolSysViewerView"`
     * `_model_module = _view_module = "molsysviewer"`
     * `_model_module_version = _view_module_version = "0.0.0"`
   * La parte de “modelo de estado rico” en Python (sincronizando una estructura de estado compleja con JS) está todavía **muy simplificada**:

     * `state: Dict` (sync=True)
     * `frame: Int` (sync=True)
   * El wrapper de alto nivel `MolSysViewer` es muy ligero: `from_empty()`, `show_test_sphere()`, `show()`, sin todavía el diseño API definitivo.

   🔖 **Para revisar en el futuro**:

   * Diseñar una **API Python más rica** (métodos tipo `.load_molsysmt_system()`, `.set_representation()`, `.add_shape()`, `.add_cavity_mesh()`, etc.).
   * Definir un **modelo de estado “declarativo”**: el usuario modifica un dict / dataclass en Python y el frontend reacciona.

2. **Arquitectura de widgets (lado JS) también simplificada**

   * `MolSysViewerModel` y `MolSysViewerView` en `js/src/widget.ts` usan `any` en varias partes para ir rápido.
   * `MolSysViewerView`:

     * Crea un `div` contenedor.
     * Instancia un `MolstarController` con ese contenedor.
     * Suscriptores de cambios de modelo (`this.model.on("change:state", ...)`) aún no explotan el estado completo.
   * No hemos hecho todavía una separación fina **controller / view / plugin**; el `MolstarController` hace de todo (bootstrap del viewer y futuro punto central para acciones).

   🔖 **Para revisar**:

   * Afinar tipos TS: usar interfaces claras para el “state” que viene de Python.
   * Separar responsabilidades:

     * `MolstarController` (maneja solo Mol*).
     * `StateController` (traduce `model.get("state")` → llamadas a Mol*).
   * Añadir tests unitarios de frontend.

3. **Elección de integración Mol*: usamos el `Viewer` “alto nivel”**

   * Finalmente usamos:

     ```ts
     import { Viewer } from "molstar/lib/apps/viewer/app";
     ```

   * Y lo instanciamos con un solo objeto:

     ```ts
     this.viewer = new Viewer({
       target: this.container,
       layoutIsExpanded: false,
       ...
     });
     this.plugin = (this.viewer as any).plugin;
     ```

   * Esta es la opción “sencilla” frente a montar explícitamente un `PluginUIContext` con `DefaultPluginSpec`, `PluginSpec`, etc.

   🔖 **Para revisar** (cuando quieras más control fino):

   * Contrastar esta solución con la arquitectura más flexible basada en `PluginContext` / `PluginUIContext`.
   * Decidir si queremos:

     * Mantener `Viewer` como capa de alto nivel, o
     * Ir directamente a la API de plugin y UI para personalizar al máximo.

4. **Ipywidgets + JupyterLab: enfoque “source extension” relativamente simple**

   * JS está en `js/` como paquete npm con:

     ```json
     "name": "molsysviewer",
     "version": "0.0.0",
     "jupyterlab": {
       "extension": "lib/index.js"
     }
     ```

   * Usamos `webpack` para generar `js/lib/index.js`.

   * Registramos el widget con un plugin simple en `js/src/index.ts`:

     ```ts
     const extension: JupyterFrontEndPlugin<void> = {
       id: "molsysviewer:plugin",
       autoStart: true,
       requires: [IJupyterWidgetRegistry],
       activate: (app, registry) => {
         registry.registerWidget({
           name: "molsysviewer",
           version: "0.0.0",
           exports: { MolSysViewerModel, MolSysViewerView },
         });
       },
     };
     ```

   * Y lo instalas como **source labextension** con `jupyter labextension install .` dentro de `js/`.

   🔖 **Para revisar**:

   * Integrar el frontend como **prebuilt/federated extension** empaquetada dentro del propio wheel del paquete Python (estilo widgets modernos).
   * Automatizar el build JS dentro del flujo `python -m build`, para que el usuario final no tenga que hacer `npm run build`.

5. **Webpack configurado a lo justo**

   * Config actual:

     * `entry: ./src/index.ts`
     * `output: lib/index.js` con `libraryTarget: "amd"`
     * `ts-loader` para TypeScript
     * `fallback` para módulos Node (`fs`, `path`, `crypto` → `false`)
     * Regla para imágenes `.png/.jpg/.gif` tipo `asset/resource`
     * `externals`: `"@jupyter-widgets/base"`, `"@jupyterlab/application"`

   🔖 **Para revisar**:

   * Dividir en `webpack.config.dev.js` y `webpack.config.prod.js`.
   * Minimizar bundle (14 MiB ahora mismo) y considerar code-splitting.
   * Re-evaluar si necesitamos todas las extensiones de Mol* (backgrounds, mp4 export, etc.).

---

## 2. Lista de cuestiones pendientes / TODOs futuros

Un checklist de cosas que están claramente **pendientes de implementar o mejorar**:

### A. Visualización y geometrías

* [ ] Implementar de verdad `drawTestSphere`:

  * Crear un `Shape` con una esfera usando la API de Mol* (builders.shape / primitives.sphere).
  * Añadirlo al árbol de estado con el `plugin`.
  * Ajustar color y opacidad.
* [ ] Añadir soporte para:

  * [ ] **Malla de cavidades** (superficies cerradas).
  * [ ] **“Nubes” de puntos** (densidades, cavidades tipo scatter).
  * [ ] **Mallas abiertas** (interfaces, bocas, canales).
* [ ] Controlar representaciones básicas:

  * `cartoon`, `sticks`, `surface`… para estructuras moleculares.
* [ ] Implementar correctamente `setFrame(index)` para trayectorias de MD.

### B. Integración con MolSysMT y otros adaptadores

* [ ] Diseño de adaptadores Python → viewer:

  * [ ] `from_molsysmt_system(system, coordinates=None, ...)`
  * [ ] Adaptadores para archivos PDB, mmCIF, DCD, etc.
* [ ] Definir un formato API intermedio para:

  * Geometrías (esferas, mallas, polígonos, líneas).
  * Cavidades detectadas con TopoMT.
* [ ] Implementar un primer pipeline end-to-end:

  * MolSysMT carga sistema → TopoMT detecta cavidades → MolSysViewer las dibuja.

### C. API Python de alto nivel

* [ ] Diseñar API del lado Python:

  * Métodos tipo:

    * `viewer.load_system(system, topology=None)`
    * `viewer.add_cavity_mesh(cavity, color, opacity)`
    * `viewer.show_hbonds(hbonds_by_frame)`
  * Manejo de “escenas” y “capas”.
* [ ] Documentar claramente qué es “estable” y qué está en `experimental`.

### D. Modelo de estado sincronizado

* [ ] Definir un esquema de `state` (dict) más explícito:

  * Por ejemplo: `{ structures: [...], shapes: [...], frames: {...}, camera: {...} }`
* [ ] En `MolSysViewerView`, añadir listeners para:

  * Cambios en `state`: aplicar diferencias sin rehacer toda la escena.
  * Cambios en `frame`: avanzar en trayectorias.

### E. Eventos del usuario y comunicación de vuelta a Python

* [ ] Capturar eventos de selección/picking en Mol* (clic sobre átomo/forma).
* [ ] Mandar eventos de vuelta a Python (por ejemplo, `on_click`, `on_pick`).
* [ ] Integrar con callbacks o señales en el lado Python.

### F. Infraestructura / empaquetado / calidad

* [ ] Empaquetar frontend como prebuilt labextension dentro del wheel:

  * De forma similar a otros widgets modernos (sin necesidad de `labextension install .` manual).
* [ ] Añadir tests:

  * Python: tests unitarios del wrapper, adaptadores, etc.
  * JS: tests básicos del `MolstarController` y del manejo de estado.
* [ ] Integración continua (CI) para:

  * Lint + tests Python (pytest).
  * Lint + build JS (tsc, webpack).
  * Chequeo de que la extensión se registra correctamente en JupyterLab.
* [ ] Documentación:

  * Guía de usuario.
  * Guía de desarrollador (especialmente la parte JS/molstar).
  * Ejemplos de notebooks.

---

## 3. Descripción de la evolución, estado actual y planes

### Evolución hasta ahora

1. **Fase de evaluación**
   Partíamos de:

   * NGLView y otros visores (molview, py3Dmol, py2Dmol, Mol*, etc.).
   * El objetivo: un visor propio, integrado con MolSysMT/TopoMT, que soporte:

     * Trayectorias de MD.
     * Representaciones moleculares estándar.
     * Objetos “topográficos” (cavidades, bocas, interfaces…).

2. **Decisión de base tecnológica**
   Se optó por:

   * Backend de visualización: **Mol*** (Mol* Viewer).
   * Integración en Jupyter: **ipywidgets + JupyterLab extension**.
   * Paquete Python: `molsysviewer`.
   * Paquete JS: `js/` con TypeScript + Webpack.

3. **Primera integración funcional (lo que hemos conseguido ahora)**

   * Creación de un **widget DOM** en Python (`MolSysViewerWidget`).
   * Creación de la contrapartida en TypeScript:

     * `MolSysViewerModel` / `MolSysViewerView`.
     * `MolstarController`, que instancia un `Viewer` de Mol* dentro de un `<div>`.
   * Configuración de Webpack 5 para:

     * Compilar TS → `lib/index.js`.
     * Resolver dependencias de Mol* (incluyendo imágenes y módulos Node).
   * Registro del widget en JupyterLab con un plugin simple (`index.ts`).
   * Instalación como **source extension** via `jupyter labextension install .`.
   * Confirmación de que:

     * El widget se crea sin errores.
     * El viewer de Mol* se inicializa dentro del widget.
     * Las llamadas desde Python (`show_test_sphere`) llegan a `drawTestSphere` en JS (aunque aún sea stub).

### Estado actual

* El **esqueleto funcional** está listo:

  * Paquete Python instalable.
  * Labextension instalable.
  * Mol* Viewer corriendo en un widget de JupyterLab.
* La comunicación Python → JS funciona:

  * Podemos pasar opciones y comandos básicos (`drawTestSphere` ya recibe los datos).
* La comunicación JS → Python aún **no está implementada** (no hay eventos devueltos).
* La parte de visualización avanzada (cavidades, mallas, trayectorias) aún no se ha implementado; está en la hoja de ruta.

### Planes inmediatos (corto plazo)

1. **Hacer que `drawTestSphere` dibuje una esfera real**:

   * Usar el API de shapes de Mol*.
   * Ver la esfera blanca translúcida en `(0, 0, 0)` desde Python.

2. **Añadir un primer método real de carga de estructura**:

   * `MolSysViewer.from_pdb_string(...)` o similar.
   * Mostrar una estructura simple en representación `cartoon`.

3. **Definir el primer “adapter” desde MolSysMT**:

   * Por ejemplo: `from_molsysmt_system(system)` que cargue un sistema y muestre la estructura en Mol*.

### Planes a medio/largo plazo

* Definir un **API estable** para:

  * manejo de sistemas,
  * trayectorias,
  * cavidades y otros elementos topográficos,
  * composición de escenas.
* Integrar MolSysViewer con:

  * MolSysMT (sistemas y trayectorias).
  * TopoMT (cavidades, bocas, interfaces).
* Optimización y ergonomía:

  * Soporte de escenas grandes,
  * botones/paneles de control en el lado JS (UI básica tipo “dashboard”).
* Empaquetar y publicar:

  * En PyPI y/o conda-forge.
  * Documentación clara y ejemplos para usuarios externos.

---

## 4. Secuencia de órdenes para clonar e instalar todo hasta `view.show()`

### Requisitos previos

* Tener **conda/mamba** (recomendable) y **Node.js** (si no, lo metemos en el entorno).
* JupyterLab 4.x.

### 4.1. Clonar el repositorio

```bash
git clone git@github.com:uibcdf/molsysviewer.git
# o: git clone https://github.com/uibcdf/molsysviewer.git

cd molsysviewer
```

### 4.2. Crear y activar entorno conda

Ejemplo con `mamba` y Python 3.12 (ajusta nombre/env a lo que prefieras):

```bash
mamba create -n molsysviewer@uibcdf_3.12 python=3.12 nodejs -y
mamba activate molsysviewer@uibcdf_3.12
```

Si no quieres meter `nodejs` en conda y ya tienes Node instalado globalmente, puedes omitirlo.

### 4.3. Instalar dependencias Python básicas

Por si el repo aún no las declara todas en `pyproject.toml`, aseguramos:

```bash
pip install jupyterlab ipywidgets
```

*(Si ya vienen como deps del paquete, esto será redundante pero inofensivo.)*

### 4.4. Instalar y construir la parte JS (labextension)

Desde el subdirectorio `js/`:

```bash
cd js

# Instala dependencias JS
npm install

# Construye el bundle frontend (TypeScript -> lib/index.js)
npm run build

# Instala la extensión de JupyterLab desde este paquete
jupyter labextension install .
```

> Este comando hace que JupyterLab conozca la extensión `molsysviewer` y pueda cargar el widget.

Vuelve a la raíz del repo:

```bash
cd ..
```

### 4.5. Instalar el paquete Python en modo editable

```bash
pip install -e .
```

Esto instala `molsysviewer` en el entorno actual, apuntando al código local (útil para desarrollo).

### 4.6. Lanzar JupyterLab y probar el widget

```bash
jupyter lab
```

En el navegador, crea un notebook con el mismo entorno (`molsysviewer@uibcdf_3.12`) y en una celda:

```python
from molsysviewer import MolSysViewer

view = MolSysViewer.from_empty()
view.show_test_sphere()  # por ahora solo llama al stub JS
view.show()
```

Qué debe ocurrir hoy:

* No hay errores en la celda.
* No hay errores rojos de JS en la consola.
* Se crea un área de widget donde Mol* inicializa su viewer (aunque aún no dibuje la esfera como tal).

---

Con esto tienes un **checkpoint completo**:

* Qué hemos hecho.
* Qué hemos simplificado (y marcado para refinar).
* Qué falta por implementar.
* Y cómo resucitar el proyecto desde un `git clone` hasta `view.show()`.

Cuando lo retomemos, podemos empezar directamente por donde lo dejaste:
convertir `drawTestSphere` en la primera “pieza visual real” de MolSysViewer y
luego seguir con adaptadores y cavidades.
