# 📌 **MolSysViewer — Checkpoint de desarrollo**

## 1. **Qué hemos aprendido**

### ▶ Mol* internamente **tiene los mecanismos necesarios** para construir y visualizar shapes propios

Ya vimos dónde están:

* `ShapeRepresentation` en `mol-repr/shape/representation.ts`
* `MeshBuilder` y sus primitivas (`addSphere`, `addCylinder`, `addMesh`, etc.)
* Módulos auxiliares para formas complejas (`shapeFromPly`, etc.)

Esto confirma que Mol* **sí puede generar esferas, superficies, cavidades y
cualquier objeto geométrico** que necesitaremos para TopoMT, ElastNetMT,
PharmacophoreMT, etc.

### ▶ El import `mol-model/shape/builders` que intentábamos usar **no existe**

Mol* cambió su arquitectura. Los builders actuales están dispersos entre:

* `mol-geo/geometry/mesh/builder/*`
* `mol-repr/shape/representation.ts`
* `mol-geo/primitive/*`

Por tanto, **necesitamos construir nuestras shapes usando directamente las APIs reales**:

* `MeshBuilder.createState()`
* `MeshBuilder.addSphere()`
* `MeshBuilder.getMesh()`
* `Shape.create()`
* y luego `ShapeRepresentation(...)`.

### ▶ MolSysViewer *sí puede* generar una esfera simple, pero el viewer **no se
está mostrando correctamente en Jupyter**

Sí se crean instancias del viewer (vemos logs correctos).
Pero:

* El canvas `<div class="molsysviewer-container">` queda muy pequeño (altura mínima).
* El widget falla al renderizar (“widget model not found”).
* El kernel se reinicia → indica **problemas con la integración JupyterLab + la labextension**.

Esto nos demuestra que **la parte más problemática no es Mol***, sino **el sistema de labextension clásico**.

### ▶ Las labextensions clásicas de JupyterLab son frágiles y cada vez menos recomendadas

Hemos visto:

* Rebuilds lentos (`jupyter lab build`).
* Errores 500 difíciles de depurar.
* “widget model not found”.
* Errores de comunicación kernel ↔ frontend.
* Incompatibilidades de JupyterLab 4.x con extensiones clásicas.

➡ Conclusión: **no es sostenible a largo plazo para un proyecto científico serio**.

### ▶ El repositorio `ipymolstar` demuestra un enfoque moderno, limpio y exitoso

Su arquitectura:

* no usa labextension clásica,
* usa un widget ligero,
* empaqueta el frontend con bundling moderno,
* evita conflictos con Jupyter.

Muestra cómo embutir Mol* en un widget **robusto y fácil de instalar** → ideal
para MolSysViewer.

### ▶ anywidget es totalmente compatible con Mol*

Permite:

* sincronizar frontend ↔ Python,
* renderizar escenas 3D complejas,
* distribuir el paquete sin build de labextensions,
* aislamiento de dependencias,
* API limpia y mantenible.

Y, muy importante:

**no limita ninguna de las funcionalidades que queremos implementar**.

---

## 2. **Dónde estamos ahora**

### ✔  Ya tenemos:

* MolSysViewer con su arquitectura Python ↔ JS definida.
* Webpack funcionando correctamente.
* `MolstarController` y el plugin inicial operativo.
* Entendimiento sólido de cómo crear geometry + shape para una esfera.
* Taglines y narrativa del proyecto definidas para README, web y GitHub.
* El repositorio de Mol* estudiado y comprendido para shapes/meshes.

### ✘ Pero:

* La integración mediante labextension **no está funcionando bien**.
* El widget no se renderiza en Jupyter (canvas minúsculo, kernel reinicia).
* La instalación es frágil y no reproducible.
* Este camino va a dar muchos problemas futuros.

---

## 3. **Siguientes pasos (ordenados y realistas)**

### **STEP 1 → Migración ordenada hacia el modelo tipo ipymolstar**

Adoptar:

```
molstar-frontend/  → bundler moderno (vite / webpack)
molstar_widget.py  → anywidget
```

Mol* sigue igual, sólo cambia la integración con Jupyter.

Esto:

* elimina la necesidad de labextension,
* arregla los errores de “widget model not found”,
* simplifica la vida a tus usuarios,
* te permite progresar rápido sin atascos.

### **STEP 2 → Extraer el frontend en un fichero propio (`MolSysViewerFrontend`)**

Armar un módulo JS claro:

* `MolSysViewerFrontend.init(container)`
* `MolSysViewerFrontend.addSphere(...)`
* `MolSysViewerFrontend.loadPDB(...)`
* etc.

### **STEP 3 → Crear un widget de anywidget minimal inicial**

Un primer prototipo:

```python
class MolSysViewer(anywidget.AnyWidget):
    _esm = Path("dist/molsysviewer.js").read_text()
    ...
```

Con un `div` que sí respeta tamaño y se renderiza sin conflictos.

### **STEP 4 → Reconstruir `addSphere()` usando las APIs correctas de Mol***

1. Crear un mesh con `MeshBuilder`.
2. Generar un `Shape`.
3. Crear un `ShapeRepresentation`.
4. Añadirlo al plugin.

Esto ya sabemos hacerlo.

### **STEP 5 → Añadir API Python**

* `viewer.add_sphere(center, radius)`
* `viewer.add_mesh(vertices, indices)`
* `viewer.show(structure)`
* `viewer.clear()`

Con mensajes Python↔JS.

### **STEP 6 → Integrar MolSysMT, TopoMT, etc.**

Una vez el viewer es estable, enchufar:

* Mallas de pockets,
* Alpha-spheres,
* Redes elásticas,
* Farmacóforos,
* Volúmenes,
* Trayectorias.

---

## 4. **Información crítica para reiniciar con seguridad**

### 💡 Arquitectura recomendada

```
molsysviewer/
    python/
        molsysviewer/
            __init__.py
            widget.py   ← anywidget aquí
    js/
        src/
            MolSysViewerFrontend.ts  ← tu plugin JS
        package.json
        vite.config.js (o webpack)
        dist/
```

### 💡 Mol* sólo necesita tu `<div>` + un bundle con tus configuraciones

No necesita labextension.
No necesita Jupyter-specific plumbing.

### 💡 La API para shapes correcta está en:

* `mol-repr/shape/representation.ts`
* `mol-geo/geometry/mesh/builder/*`
* `mol-geo/primitive/sphere`

### 💡 El error actual de Jupyter NO es de Mol*

Es consecuencia de la labextension clásica.
Migrar a anywidget lo elimina por completo.

---


Siguiente paso: **Montamos el nuevo esqueleto de “MolSysViewer” casi desde cero.**
