# Propuesta de Mejora: Persistencia del Color de Fondo (Corrección de Pérdida en Reconstrucción y Exportaciones)

## 1. Contexto y Diagnóstico

En MolSysViewer, el usuario puede personalizar el entorno visual del escenario estableciendo el color de fondo a través de `SceneManager` en `molsysviewer/scene.py`. Esto envía mensajes directos al frontend:
* Para temas rápidos: `self._view._send({"op": "toggle_background", "mode": "light"})`
* Para colores específicos: `self._view._send({"op": "set_background_color", "color": color_int})`

El problema crítico es que **el color de fondo no se almacena como una propiedad persistente en el estado del backend de Python**. Se trata como un evento "fire-and-forget" (disparar y olvidar) que solo queda registrado temporalmente en el historial de mensajes de la sesión activa (`self._message_history`).

Cuando ocurre una mutación estructural del sistema molecular (por ejemplo, al añadir o eliminar átomos con `view.remove()` o reconstruir el visor con `_rebuild_view_from_current_molsys()`), el backend ejecuta lo siguiente:
```python
# Rebuild the message history to reflect the new state (important for HTML exports).
self._message_history = []
self._pending_messages = []

self._send({"op": "clear_all"})
self._send({"op": "load_molsys_payload", ...})
```

Al limpiar por completo `self._message_history` (línea 1018 de `core.py`), **cualquier mensaje previo de cambio de color de fondo se elimina de forma permanente**. Aunque el backend restaura manualmente las capas activas, las representaciones y las regiones en los bucles posteriores de reconstrucción, **no cuenta con ningún registro de la preferencia de color de fondo**, lo que provoca que el visor reconstruido revierta incondicionalmente al tema por defecto (generalmente negro/oscuro).

Además, en `_build_export_messages()` (método encargado de empaquetar el estado para generar las exportaciones a archivos HTML estáticos o regenerar el visor en nuevas celdas de Jupyter), el color de fondo no se inyecta de forma garantizada si el historial fue limpiado previamente, provocando inconsistencias visuales en los reportes exportados por los investigadores.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Inconsistencia Visual en Flujos de Trabajo**: Un usuario que ha configurado meticulosamente su visor con un fondo blanco para preparar figuras de alta calidad ve cómo su preferencia se destruye y el visor vuelve a negro tan pronto como realiza una edición molecular menor o cambia el estado de la trayectoria.
* **Exportaciones HTML Corruptas**: Los archivos HTML independientes exportados para compartir con colaboradores o incluir en páginas web de soporte pierden la configuración del color de fondo del tema seleccionado, mostrándose con el tema opuesto o predeterminado.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

Se propone integrar la preferencia del color de fondo como un ciudadano de primera clase en el estado del backend de Python y garantizar su restauración automática en los ciclos de reconstrucción y exportación:

### Propuesta: Almacenamiento Persistente en el Estado del Backend
1. **Definir Atributo de Estado**:
   Agregar un atributo `_background_color_state` (o similar) en la inicialización de `MolSysView` en `molsysviewer/viewer/core.py` para almacenar la última preferencia establecida:
   ```python
   # En __init__:
   self._background_color_state: dict | None = None
   ```

2. **Actualizar el Estado al Enviar el Mensaje**:
   Interceptar los mensajes de fondo en `SceneManager.set_background` para guardar la preferencia en el backend:
   ```python
   def set_background(self, color: Any = "dark") -> None:
       if isinstance(color, str) and color.strip().lower() in ("light", "dark"):
           mode = color.strip().lower()
           self._view._background_color_state = {"op": "toggle_background", "mode": mode}
           self._view._send(self._view._background_color_state)
           return
       color_int = normalize_color(color)
       self._view._background_color_state = {"op": "set_background_color", "color": color_int}
       self._view._send(self._view._background_color_state)
   ```

3. **Restaurar el Color en Reconstrucciones**:
   En el método `_rebuild_view_from_current_molsys`, después de cargar el nuevo payload molecular, enviar la preferencia de fondo almacenada si existe:
   ```python
   if self._background_color_state is not None:
       self._send(self._background_color_state)
   ```

4. **Garantizar su Inclusión en Exportaciones**:
   En `_build_export_messages()` en `molsysviewer/viewer/export.py`, asegurar que el mensaje de color de fondo se inyecta explícitamente en la secuencia de mensajes de reconstrucción si el usuario configuró uno personalizado.

---

## 4. Criterios de Aceptación

1. Si un usuario cambia el color de fondo del visor (ej. a blanco) y posteriormente muta la estructura molecular o elimina átomos con `view.remove()`, el visor debe retener el color de fondo blanco de forma automática sin que el usuario tenga que volver a configurarlo.
2. Los archivos HTML exportados estáticamente deben preservar el color de fondo exacto configurado por el usuario en la sesión de Jupyter.
3. Se deben definir pruebas unitarias que verifiquen que la propiedad de color de fondo persiste en el objeto del visor tras simular una reconstrucción del sistema y que se inyecta correctamente en el vector de mensajes devuelto por `_build_export_messages()`.
