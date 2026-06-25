# Propuesta de Mejora: Remapeo de Índices de Anclaje de Anotaciones ante Cambios en la Topología

## 1. Contexto y Diagnóstico

MolSysViewer permite añadir anotaciones en 3D (etiquetas) ancladas a átomos específicos mediante `AnnotationsManager` en `molsysviewer/annotations.py`. Estas anotaciones resuelven sus anclajes llamando a `_resolve_anchor_atom_indices`, que mapea una selección o una lista de átomos a una lista plana de índices de átomo absolutos (`list[int]`) basados en el estado actual del sistema molecular.

Por otro lado, la librería ofrece la capacidad de editar interactivamente el sistema molecular en tiempo de ejecución. El método `remove` de `molsysviewer/viewer/molsysmt_interface.py` permite eliminar átomos y estructuras de la vista activa y del objeto `_molsys` subyacente. Al eliminar átomos, los índices del sistema molecular restante se desplazan (remap).

Para evitar que los objetos del escenario queden desalineados, el método `_rebuild_view_from_current_molsys` en `molsysviewer/viewer/core.py` implementa un remapeo de índices utilizando un mapa de traducción (`atom_index_map: dict[int, int]`). Sin embargo, **este remapeo se aplica únicamente a las regiones**:
```python
if atom_index_map is not None:
    for region in self._regions.values():
        if region.atom_indices is None:
            continue
        region.atom_indices = tuple(self._remap_indices(list(region.atom_indices), atom_index_map))
```

Las anotaciones almacenadas en el historial (`self._annotation_history` y los objetos `Annotation` en `self._layers`) **son completamente omitidas en este proceso de traducción**. Como resultado, sus listas internas de `atom_indices` permanecen apuntando a los índices absolutos antiguos del sistema molecular previo a la eliminación de los átomos.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Etiquetas Desplazadas o Huérfanas**: Si un usuario tiene un sistema molecular con una proteína y agua, crea una anotación en la cadena lateral del residuo clave Lys120 (ej. átomos con índices 1500-1510), y posteriormente ejecuta `view.remove(selection="water")` para limpiar el disolvente y enfocar la visualización, todos los índices de átomos se desplazan. Dado que la anotación conserva los índices 1500-1510, esta saltará visualmente a un átomo completamente diferente de la proteína (o desaparecerá si el nuevo índice máximo es menor que 1500), quedando huérfana o señalando un residuo científicamente incorrecto.
* **Inconsistencia del Escenario**: La desincronización de índices genera frustración en el usuario, obligándolo a eliminar y volver a crear manualmente todas las anotaciones tridimensionales cada vez que realiza una limpieza o recorte de la estructura.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

Se propone extender la lógica de remapeo de índices dentro de `_rebuild_view_from_current_molsys` para abarcar las anotaciones (y mediciones) registradas en el visor.

### Propuesta: Remapeo de Índices en el Historial de Anotaciones
1. **Actualizar Historial de Mensajes y Capas Activas**:
   Durante el proceso de reconstrucción en `_rebuild_view_from_current_molsys`, iterar sobre las anotaciones existentes y traducir sus índices de anclaje:
   ```python
   if atom_index_map is not None:
       # 1. Remapear regiones (comportamiento actual)
       # ...
       
       # 2. Remapear anotaciones en las capas activas
       for layer in self._layers.values():
           if getattr(layer, "kind", None) == "annotation":
               # Asumiendo que el objeto Annotation almacena sus índices en un atributo expuesto
               old_indices = getattr(layer, "atom_indices", None)
               if old_indices:
                   layer.atom_indices = self._remap_indices(list(old_indices), atom_index_map)
       
       # 3. Remapear el historial de mensajes de anotaciones para mantener consistencia en exportaciones
       rewritten_annotations = []
       for msg in self._annotation_history:
           updated = dict(msg)
           opts = updated.get("options")
           if isinstance(opts, dict) and "atom_indices" in opts:
               opts = dict(opts)
               opts["atom_indices"] = self._remap_indices(opts["atom_indices"], atom_index_map)
               updated["options"] = opts
           rewritten_annotations.append(updated)
       self._annotation_history = rewritten_annotations
   ```

2. **Manejo de Átomos Eliminados**:
   Si los átomos de anclaje de una anotación son completamente eliminados del sistema (es decir, `self._remap_indices` devuelve una lista vacía porque los índices antiguos no existen en el mapa), la anotación correspondiente debe desactivarse o eliminarse automáticamente para evitar representar datos flotantes sin sentido en el espacio 3D.

---

## 4. Criterios de Aceptación

1. Tras ejecutar una eliminación de átomos mediante `view.remove()`, las anotaciones existentes que permanezcan en el sistema molecular reconstituido deben seguir ancladas visual y geométricamente a los mismos átomos físicos originales.
2. Si los átomos que sirven de anclaje a una anotación son eliminados en su totalidad, la anotación debe ser removida limpiamente del escenario y de los historiales internos sin lanzar excepciones.
3. Se deben incorporar pruebas de integración E2E/unitarias donde se cargue una estructura, se añada una anotación a un átomo específico de la proteína, se elimine una porción de agua/iones del sistema, y se verifique que la anotación permanece asociada al átomo correcto mediante la validación de sus índices de anclaje remapeados.
