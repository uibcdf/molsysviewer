# Propuesta de Mejora: Sincronización de Historial en Renombrado de Capas (Re-tagging Desync)

## 1. Contexto y Diagnóstico

MolSysViewer permite agrupar objetos de escena (`shapes`, `annotations`, `measurements`) en capas organizativas. La clase `LayerHandle` en `molsysviewer/layers.py` expone el método `set_tag(self, new_tag)` (línea 194) para renombrar una capa en caliente. Esto envía un comando `"op": "set_layer_tag"` al frontend y re-registra la capa en el diccionario interno de Python a través de `_reregister_layer`.

El problema de reproducibilidad radica en que **los comandos de inicialización previos de los objetos de la capa no se actualizan en el historial de mensajes de Python**. 

*Ejemplo de Flujo Anómalo*:
1. El usuario crea una esfera asignándola a la capa `"pocket_1"`:
   - Se añade al historial de shapes: `{"op": "add_sphere", "options": {"tag": "s1", "layer_tag": "pocket_1"}}`.
2. El usuario renombra la capa de `"pocket_1"` a `"active_site"`:
   - Se envía el mensaje: `{"op": "set_layer_tag", "tag": "pocket_1", "new_tag": "active_site"}`.
   - En el frontend de JS, la capa se renombra y la esfera se re-asocia correctamente en caliente.
3. Sin embargo, en el historial de Python (`_shape_history`), el mensaje original de la esfera sigue teniendo `"layer_tag": "pocket_1"`.
4. Si el kernel se reinicia o se invoca un `rebuild()` del visor desde el historial, MolSysViewer ejecutará primero la creación de la esfera en `"pocket_1"`, y luego intentará renombrar la capa `"pocket_1"` (que puede haber quedado vacía o inexistente en otros contextos), provocando estados inconsistentes o huérfanos.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Pérdida de la Reproducibilidad del Lienzo**: Al volver a cargar el notebook o reconstruir la escena desde el historial de comandos guardados, el visor no reflejará fielmente la estructura de capas que el usuario configuró interactivamente. Algunos objetos visuales volverán a sus capas antiguas obsoletas o no se agruparán de forma correcta.
* **Inconsistencia de Gestión**: Las operaciones sucesivas de mostrar/ocultar capas programáticamente en Python fallarán al operar sobre capas cuyos miembros históricos quedaron dispersos debido a la falta de actualización en el historial.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Reescritura Reactiva de la Historia en el Mixin de Replay

Se propone modificar `HistoryMixin` en `molsysviewer/viewer/history.py` para capturar el comando `set_layer_tag` y reescribir retroactivamente todos los mensajes del historial asociados a la capa modificada:

1. **Interceptar `set_layer_tag` en la Historia**:
   En el método `_record_shape_message` y equivalentes en `history.py`, interceptar de forma consistente el renombrado de capas:
   ```python
   if op == "set_layer_tag":
       old_tag = msg.get("tag")
       new_tag = msg.get("new_tag")
       if not isinstance(old_tag, str) or not isinstance(new_tag, str):
           return
       
       # Función interna para reescribir el layer_tag de los mensajes
       def rewrite_layer_tag(item: dict) -> dict:
           options = item.get("options")
           if isinstance(options, dict) and options.get("layer_tag") == old_tag:
               updated = dict(item)
               updated_options = dict(options)
               updated_options["layer_tag"] = new_tag
               updated["options"] = updated_options
               return updated
           return item

       # Reescribir retroactivamente todos los historiales afectados en Python
       self._shape_history = [rewrite_layer_tag(m) for m in self._shape_history]
       self._annotation_history = [rewrite_layer_tag(m) for m in self._annotation_history]
       self._measurement_history = [rewrite_layer_tag(m) for m in self._measurement_history]
       self._message_history = [rewrite_layer_tag(m) for m in self._message_history]
       return
   ```

2. **Garantizar Consistencia**:
   Este enfoque asegura que cualquier comando `"add_*"` previo en el historial de replay quede permanentemente actualizado con la referencia al nuevo tag de la capa, eliminando cualquier inconsistencia tras la reconstrucción.

---

## 4. Criterios de Aceptación

1. Renombrar una capa mediante `layer.set_tag(new_tag)` debe actualizar retroactivamente el atributo `layer_tag` de todos los comandos de creación de objetos pertenecientes a esa capa en el historial de mensajes de Python.
2. Tras invocar un `rebuild()` del visor en caliente, la escena debe reconstruirse con la estructura y nombres de capas finales actualizados, libre de referencias a capas obsoletas.
3. Se deben añadir pruebas de regresión que verifiquen que el historial de shapes y de mensajes queda reescrito correctamente tras renombrar una capa que contiene múltiples miembros geométricos.
