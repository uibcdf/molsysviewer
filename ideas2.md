# 1. **Contexto general**

MolSysViewer es el nuevo visor interactivo basado en **Mol★** e implementado con **anywidget**.
Está diseñado para integrarse profundamente con:

* **MolSysMT** (núcleo del ecosistema)
* **TopoMT** (detección y análisis topográfico de cavidades)
* **PharmacophoreMT** (representación de elementos farmacofóricos)

Este checkpoint resume:

* **Shapes futuras previstas**
* **Tareas técnicas asociadas**
* **Integración con MolSysMT y TopoMT**
* **Roadmap inmediato y de mediano plazo**

Es el documento central para retomar el desarrollo del subsistema de shapes.

---

# 2. **Shapes planificadas para el futuro**

A continuación se listan las formas 3D (shapes) que se han identificado como necesarias para MolSysViewer, tanto para visualización molecular general como para integración profunda con TopoMT y PharmacophoreMT.

---

## 2.1. **Esfera transparente avanzada**

* Transparencia con blending correcto.
* Depth sorting para escenas complejas.
* Control detallado de color y alpha.
* Permitir colecciones (ShapeGroup).

---

## 2.2. **Cajas (boxes) / hexaedros**

* Útiles para:

  * bounding boxes
  * regiones de interés espaciales
  * recortes (focus/volume cropping)
* Opción de líneas o superficies.

---

## 2.3. **Cilindros y segmentos**

* Representar:

  * ejes principales
  * vectores geométricos
  * enlaces estilizados
  * normales

---

## 2.4. **Conos y flechas**

* Dirección de fuerzas, gradientes o campos.
* Direccionalidad farmacofórica (D→A).
* Flechas combinadas con cilindros.

---

## 2.5. **Superficies trianguladas (meshes)**

* Para:

  * mallas de cavidades
  * superficies detectadas por TopoMT
  * isosurfaces simples
  * superficies custom cargadas por el usuario
* Soporte para:

  * color por vértice
  * alpha
  * shaders simples

---

## 2.6. **Nubes de puntos (point clouds)**

* Representar:

  * alpha-esferas crudas
  * datos no estructurados
  * volumen muestreado
  * puntos farmacofóricos densos

---

## 2.7. **Polilíneas / splines**

* Para:

  * trayectorias de átomos o COM
  * rutas geométricas
  * caminos generados por análisis topográfico

---

## 2.8. **Labels / marcadores 3D**

* Texto flotante en la escena.
* Controles:

  * tamaño
  * color
  * fondo semitransparente
  * ocultar/mostrar grupos de labels

---

## 2.9. **Shapes compuestos (ShapeGroup)**

* Grupos de:

  * esferas
  * cilindros
  * flechas
  * mallas
* Operaciones:

  * show/hide/isolate
  * update parcial
  * borrado completo del grupo

---

## 2.10. **Shapes especializados para TopoMT**

### 2.10.1. **Alpha-esferas agrupadas por concavidad**

* Coloreadas por clúster.
* Transiciones suaves entre concavidades.
* Opciones:

  * transparencia
  * modos de densidad

### 2.10.2. **Superficies de concavidades**

* Mesh generada a partir del análisis topográfico.
* Opción de “shell thickness”.

### 2.10.3. **Mouths y BaseRims**

* Círculos, elipses o loops 3D.
* Colores distintivos por tipo (boundary concavity/convexity).

### 2.10.4. **Interfaces convexas/mixtas**

* Ribbons o superficies delgadas.
* Delimitación visual clara de zonas mixtas.

---

# 3. **Roadmap técnico para Shapes y Rendering**

## 3.1. **Protocolos Python ↔ JS**

* Consolidar `viewer_json.py` y `universal_json.py`.
* Unificar formato de mensajes para todas las shapes.
* Tipado estricto y validación.

---

## 3.2. **Sistema de mensajes robusto**

* Implementar `_handle_msg` completo en JS.
* Logging interno (nivel debug + verbose).
* Manejo de errores y excepciones en JS.

---

## 3.3. **Manager de shapes**

* Registro centralizado con:

  * ID de shape
  * ID de grupo
  * tipo
  * estado (visible/hidden)
* API Python:

  * `add_shape()`
  * `remove_shape()`
  * `update_shape()`
  * `clear_shapes()`
  * `isolate_shape()`

---

## 3.4. **Multiples estructuras por viewer**

* Cargar varias estructuras simultáneamente.
* Elegir estructura activa por índice.
* Suportar:

  * PDB ID múltiples
  * archivos locales
  * objetos MolSysMT

---

## 3.5. **Trayectorias**

* Preparación del flujo:

  * frames precalculados
  * streaming (eventual)
* Visualización:

  * cartoon dinámico
  * partículas/esferas animadas

---

## 3.6. **Integración MolSysMT**

* `mol.view()` debe usar MolSysViewer.
* Envío automático de datos:

  * coordenadas
  * topología
  * bonds
  * metadata

---

## 3.7. **Integración TopoMT**

* Shapes correspondientes a:

  * concavidades
  * mouths
  * rims
  * interfaces
* API: `mol.view_topology(topomt_object)`

---

## 3.8. **Documentación**

* Tutorial Jupyter.
* Tutorial de shapes.
* Referencia de API Python.
* Referencia de API JS.

---

## 3.9. **Tests**

* Unit tests Python.
* Tests de integración con MolSysMT.
* Tests visuales (hash de escena).
* Tests de robustez del protocolo JSON.

---

## 3.10. **Pipeline TypeScript**

* Estructura recomendada:

```
js/
 └── src/
     ├── plugin/
     ├── shapes/
     ├── managers/
     ├── messages/
     ├── utils/
     └── index.ts
```

* Dividir shapes en módulos independientes.
* Generar tipos TS ↔ Python (JSON schemas simples).

---

# 4. **Roadmap inmediato (próximos pasos)**

1. **Limpiar y validar el viewer actual**

   * show/hide corretos
   * clear / clear_all
   * flujo básico de mensajes funcionando

2. **Implementación del ShapeManager (núcleo completo)**

3. **Shape 1: esfera transparente estable**

   * será la referencia para todas las demás shapes

4. **Shape 2: caja / hexaedro**

5. **Shape 3: cilindros + flechas**

6. **Shape 4: point clouds**

7. **Integración MolSysMT: `mol.view()`**

8. **Integración inicial con TopoMT (alpha-esferas)**

---

# 5. **Roadmap a medio plazo**

* Mallas topográficas completas.
* Shapes farmacofóricas.
* Trayectorias.
* Visualización volumétrica ligera.
* Optimización WebGL.
* Previsualización 2D desde Python.

