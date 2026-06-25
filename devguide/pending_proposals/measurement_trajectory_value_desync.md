# Propuesta de Mejora: Sincronización Dinámica de Valores de Medición en Trayectorias

## 1. Contexto y Diagnóstico

MolSysViewer permite calcular distancias, ángulos y dihedros sobre las estructuras cargadas. En `molsysviewer/measurements.py`, el método `_compute_measurement_value` realiza el cálculo geométrico en el backend de Python apoyándose en la utilidad `_endpoint_position_nm` (línea 239).

El problema radica en que `_endpoint_position_nm` consulta las coordenadas del sistema molecular usando `msm.get` y luego **toma incondicionalmente las coordenadas del primer frame (índice 0)** para calcular el centroide del átomo o grupo:
```python
result = msm.get(molsys, element="atom", selection=atoms, output_type="dictionary", coordinates=True, skip_digestion=True)
coords = result.get("coordinates")
# ...
arr = np.asarray(coords)  # (n_structures, n_atoms, 3) in nm
return arr[0].mean(axis=0)  # centroid of selected atoms, shape (3,)
```

Como resultado:
* Si el sistema cargado es una trayectoria dinámica (multi-frame), el valor de la medida guardado en Python en `_measurement_history` y expuesto mediante `view.measurements.info()` es **estático y corresponde únicamente al frame 0**.
* El visor en el navegador (Mol*) actualiza visualmente la línea y recalcula dinámicamente la etiqueta de texto en pantalla durante la reproducción de la trayectoria.
* El backend de Python permanece completamente desfasado, reportando una distancia o ángulo erróneo y estático en el notebook de Jupyter.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Inconsistencia de Datos Científicos**: Si un investigador utiliza celdas de Jupyter para analizar las fluctuaciones de una distancia de puente de hidrógeno a lo largo de una trayectoria mientras observa la animación, la API de Python reportará un valor plano constante (el del frame 0), invalidando el análisis cuantitativo interactivo.
2. **Quiebre de la Promesa de Estado**: Los datos inspeccionables en Python no representan fielmente lo que el usuario observa en la pantalla al avanzar la trayectoria, comprometiendo la integridad de la sesión de modelado estructural.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Indexación Basada en el Frame Activo con Fallback Seguro

Se propone modificar los métodos de cálculo en `measurements.py` para incorporar el frame activo del visor en el cálculo:

1. **Obtener el Frame Activo en el Cálculo**:
   En `_endpoint_position_nm`, utilizar el frame activo actual del reproductor (`self._view.player.index` o `_current_structure_index`) para indexar las coordenadas:
   ```python
   def _endpoint_position_nm(self, pick: list[int], ea_indices: list[int], policy: str, structure_index: int | None = None) -> "np.ndarray | None":
       # ...
       if structure_index is None:
           structure_index = self._view.player.index
       # ...
       arr = np.asarray(coords)  # (n_structures, n_atoms, 3) in nm
       # Controlar límites por si el índice del reproductor está fuera de rango
       frame_idx = min(max(0, int(structure_index)), len(arr) - 1)
       return arr[frame_idx].mean(axis=0)
   ```

2. **Cálculo Multidimensional (Trayectorias Completas)**:
   Modificar `info()` para que, si el sistema es una trayectoria, devuelva opcionalmente el valor de la medida en el frame activo actual, o un arreglo con los valores de la medida para **todos los frames de la trayectoria** (ej. `values_trajectory: list[float]`). Esto permitiría al usuario graficar instantáneamente la fluctuación de la distancia directamente desde el objeto de medida.

---

## 4. Criterios de Aceptación

1. La llamada a `view.measurements.info()` para una medición debe reportar el valor geométrico preciso correspondiente al frame activo del visualizador al momento de la consulta.
2. Si el usuario avanza la trayectoria a otro frame, el valor devuelto en Python debe actualizarse coherentemente.
3. Se debe incluir una prueba unitaria con un sistema demo multi-frame (como `dialanine`) que verifique que el valor calculado de una distancia cambia de forma precisa al desplazarse a través de diferentes índices de estructura (`go_to_structure`).
