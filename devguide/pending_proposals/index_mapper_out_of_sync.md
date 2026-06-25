# Propuesta de Mejora: Sincronización Reactiva de Indexación (Index Mapper Out-of-Sync)

## 1. Contexto y Diagnóstico

MolSysViewer utiliza un mapeador de índices (`_index_mapper` definido en `molsysviewer/viewer/index_mapper.py` e instanciado en `core.py`) para tender un puente coherente de datos:
1. Permite que el usuario opere en Python con los índices de átomos globales y originales de su estructura molecular en MolSysMT.
2. Traduce estos índices a los índices locales ordenados secuencialmente que requiere el motor gráfico de Mol* en el navegador para garantizar un renderizado estable y rápido.

El problema conceptual de acoplamiento radica en que **la topología molecular en Python se asume estática tras la carga inicial del sistema**. Si el usuario realiza ediciones dinámicas sobre la estructura en caliente en Python a mitad de una sesión interactiva (por ejemplo, eliminando un conjunto de átomos de solvente, agregando cadenas de ligandos mediante `append_structures` o editando la conectividad de los residuos):
* La estructura de datos del sistema molecular cambia en Python.
* El mapeador `_index_mapper` no se reconstruye de forma reactiva e incondicional en todas las capas del visor al realizar estas mutaciones estructurales.
* Como consecuencia, el mapa de indexación interna queda desactualizado.

---

## 2. Impacto Científico y de Experiencia de Usuario

Cuando el mapeador de índices queda desfasado tras una edición estructural, ocurren las siguientes fallas:
1. **Anotaciones y Medidas Desplazadas**: Las etiquetas tridimensionales (`annotations`) y las mediciones activas (`measurements`) que se crearon previamente comienzan a apuntar a átomos incorrectos en el espacio 3D, ya que las traducciones de índices resuelven posiciones erróneas basándose en el mapa antiguo.
2. **Fallas en Selecciones y Regiones**: Al interactuar con el lienzo o intentar activar una región guardada (`region.activate()`), el visor seleccionará un conjunto de átomos diferente al esperado, lo que compromete gravemente la reproducibilidad científica de la sesión de modelado.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta A: Reconstrucción Reactiva por Eventos Estructurales
* **Descripción**: Introducir un mecanismo de observador en `core.py`. Cada método mutador de la estructura molecular (tales como `append_structures`, `remove`, `add`, `set`) debe notificar la alteración al visor. El visor destruirá la instancia antigua de `_index_mapper` y construirá una nueva en caliente basándose en la nueva topología.
* **Mapeo de Capas Existentes**: Inmediatamente después de reconstruir el mapeador, el visor debe recorrer las colecciones activas de formas (`_shape_history`), anotaciones (`_annotation_history`) y mediciones (`_measurement_history`), y reescribir sus índices internos utilizando el nuevo mapa mediante utilidades de remapeo (como `_remap_shape_message` y `_remap_measurement_message` que ya existen en `core.py`), enviando los mensajes de actualización de coordenadas al frontend de forma síncrona.
* **Pros**: Consistencia absoluta del estado y las coordenadas de todos los objetos en escena tras cualquier edición estructural.
* **Contras**: Complejidad en el manejo del remapeo si los átomos sobre los que se construyó un objeto (ej. una medida de distancia) fueron eliminados por completo en la mutación.

---

## 4. Criterios de Aceptación

1. Cualquier alteración estructural realizada en Python a través de la API pública del visor debe disparar la regeneración automática y segura del mapeador de índices `_index_mapper`.
2. Las anotaciones y formas geométricas existentes sobre átomos que sobrevivieron a la edición estructural deben conservar su ubicación e indexación correctas en el lienzo de Mol*.
3. Si un objeto visual (ej. una etiqueta) estaba anclado a un átomo que fue eliminado del sistema molecular, la librería debe eliminar el objeto visual de la escena de forma segura o marcarlo con un estado de advertencia, en lugar de permitir que se desplace a otro átomo por errores de indexación.
