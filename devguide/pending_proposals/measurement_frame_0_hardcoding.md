# Propuesta de Mejora: Corrección de Cálculos Estáticos en Trayectorias (Hardcoding de Frame 0 en Medidas)

## 1. Contexto y Diagnóstico

En `molsysviewer/measurements.py`, la clase `MeasurementsManager` calcula distancias, ángulos y dihedros basándose en las coordenadas tridimensionales de los átomos. Cuando se solicita un cálculo de posición de un extremo (o centroide) mediante `_endpoint_position_nm`, el código recupera las coordenadas del sistema molecular a través de MolSysMT:

```python
def _endpoint_position_nm(self, pick: list[int], ea_indices: list[int], policy: str) -> "np.ndarray | None":
    ...
    result = msm.get(molsys, element="atom", selection=atoms, output_type="dictionary", coordinates=True, skip_digestion=True)
    coords = result.get("coordinates")
    if coords is None:
        return None
    arr = np.asarray(coords)  # (n_structures, n_atoms, 3) en nm
    return arr[0].mean(axis=0)  # centroid of selected atoms, shape (3,)
```

El error grave de diseño e implementación radica en la línea:
`return arr[0].mean(axis=0)`

El tensor `arr` tiene tres dimensiones: `(n_structures, n_atoms, 3)`. En la nomenclatura de MolSysMT y simulación molecular, `n_structures` representa el número de estructuras (o frames/pasos de tiempo) de una trayectoria.
Al forzar el índice `0` (`arr[0]`), **el backend de Python calcula y registra el valor de la propiedad geométrica considerando única y exclusivamente el frame 0 del sistema**.

Posteriormente, en `_compute_measurement_value`, se realiza el cálculo geométrico (ej. norma de la diferencia para distancias) que devuelve un único escalar (`float`) correspondiente a este frame inicial. Cuando el usuario invoca `view.measurements.info()`, el campo `value` contiene este único valor estático.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Incongruencia entre la UI y los Datos Cuantitativos**: Durante la reproducción de una trayectoria en el frontend, las líneas y etiquetas de medición en 3D se actualizan dinámicamente en pantalla reflejando los cambios de conformación molecular de cada frame. Sin embargo, si el investigador consulta `view.measurements.info()` desde Python para extraer datos para un análisis cuantitativo o graficar la serie temporal, los valores devueltos son constantes e incorrectos (fijos en el frame 0), invalidando los resultados del análisis.
* **Imposibilidad de Análisis de Series Temporales**: No existe ningún mecanismo en la API de Python para extraer el valor de la distancia o ángulo a lo largo de toda la trayectoria o para un frame específico diferente del primero.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Alternativa A: Retornar Series Temporales Completas (Recomendada para Análisis Cuantitativo)
Modificar `_endpoint_position_nm` y `_compute_measurement_value` para que no colapsen la dimensión temporal. En su lugar, deben calcular la propiedad geométrica para cada estructura en `n_structures` y retornar un arreglo de NumPy o una lista de cantidades (ej. usando `pyunitwizard`):
1. `arr` mantiene la forma `(n_structures, n_atoms, 3)`.
2. Calcular la posición media en cada frame: `arr.mean(axis=1)` dando forma `(n_structures, 3)`.
3. Calcular la propiedad molecular a lo largo de todos los pasos temporales, retornando una serie temporal de valores.
4. En `info()`, el campo `value` puede contener la serie temporal completa, o se puede ofrecer un método `view.measurements.series(tag)` para extraerla directamente como un objeto compatible con Pandas o NumPy.

### Alternativa B: Cálculo Dinámico basado en el Frame Activo
Si se prefiere mantener un valor escalar, el backend de Python debe conocer el frame activo del reproductor (sincronizado desde el frontend) e indexar el arreglo de coordenadas con dicho índice dinámico:
```python
active_frame = self._view.player.active_frame  # O equivalente
return arr[active_frame].mean(axis=0)
```

### Alternativa C: Enfoque Híbrido (Propuesta Óptima)
1. Almacenar la serie temporal completa en el registro interno de la medida para permitir análisis estadísticos directos en Python.
2. Sincronizar el valor escalar correspondiente al frame activo en el diccionario devuelto por `info()` para una rápida inspección.

---

## 4. Criterios de Aceptación

1. Para sistemas con múltiples estructuras (trayectorias), el valor de la medida calculado en Python no debe ser idéntico en todos los frames si la geometría molecular cambia.
2. Debe ser posible recuperar el perfil de la medida (distancia, ángulo o dihedro) a lo largo de toda la trayectoria desde el backend de Python sin necesidad de iterar manualmente sobre el visor.
3. Se deben añadir pruebas unitarias con sistemas de prueba dinámicos (como `dialanine` o `pentalanine` de `molsysviewer.demo`) que verifiquen que las distancias calculadas cambian con respecto a los índices de estructura y coinciden con los cálculos geométricos estándar de referencia.
