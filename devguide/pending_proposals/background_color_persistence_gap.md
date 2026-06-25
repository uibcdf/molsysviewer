# Propuesta de Mejora: Persistencia y Reproducibilidad del Color de Fondo de la Escena

## 1. Contexto y Diagnóstico

MolSysViewer permite alterar las propiedades cosméticas de la escena, incluyendo el color de fondo del lienzo tridimensional (transparente, blanco, negro, o gradientes personalizados). Esta alteración puede realizarse de forma interactiva a través de los paneles de configuración en el frontend, o programáticamente en Python mediante el gestor de escena (`view.scene.set_background_color(...)`).

El problema de reproducibilidad radica en que **el color de fondo de la escena no se captura en el historial de mensajes de exportación**. Cuando se invoca a `_build_export_messages()` en `molsysviewer/viewer/core.py` para serializar el estado visual completo de la sesión científica (ej. para guardar el estado del notebook, reconstruir el visor tras una recarga del kernel o exportar un estado estático a una página HTML interactiva):
1. El historial de mensajes contiene los comandos para regenerar regiones, representaciones, anotaciones, mediciones y la posición de la cámara.
2. Sin embargo, **el comando del color de fondo seleccionado se omite por completo del historial reconstruido**.
3. Al volver a abrir la sesión o renderizar el visor exportado, la escena se inicializa incondicionalmente con el color de fondo por defecto (transparente o negro).

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Quiebre de la Reproducibilidad Estética**: Si un investigador dedica tiempo a configurar una escena limpia con un fondo blanco impecable para ilustrar una interacción ligando-proteína y decide exportar la sesión para compartir el notebook, otros investigadores que abran el cuaderno verán la molécula renderizada sobre el fondo negro por defecto. Las anotaciones y etiquetas oscuras pueden volverse completamente invisibles debido al contraste inapropiado, arruinando la figura científica.
2. **Inconsistencia en Páginas HTML Exportadas**: Las exportaciones HTML estáticas interactivas pierden la configuración de color de fondo del visor original, degradando la fidelidad de las figuras científicas embebidas en reportes y artículos web.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Integración de Atributos del Entorno en la Reconstrucción de la Escena

Se propone incluir la persistencia de las propiedades de entorno y lienzo en el historial de replay:

1. **Almacenar la Configuración del Entorno**:
   Añadir un diccionario de estado de entorno en `core.py` (ej. `self._environment_settings: dict[str, Any]`) para almacenar propiedades como el color de fondo, la visibilidad de la cuadrícula, los parámetros de niebla (*fog*) y la iluminación de la escena.
   
2. **Interceptar y Registrar el Comando**:
   Cuando el usuario o la UI llame a `set_background_color`, registrar la operación en la colección de historia de replay:
   ```python
   def set_background_color(self, color: Any, *, skip_digestion: bool = False) -> None:
       # ...
       msg = {"op": "set_background_color", "color": normalize_color(color)}
       self._view._send(msg)
       self._view._environment_settings["background_color"] = normalize_color(color)
   ```

3. **Serializar en el Replay de Exportación**:
   Modificar `_build_export_messages()` en `core.py` para que lea el diccionario `_environment_settings` y anexe los mensajes de configuración del entorno al inicio de la lista de mensajes exportados, garantizando que el lienzo se configure con el color de fondo correcto antes de renderizar la topología y los objetos visuales.

---

## 4. Criterios de Aceptación

1. El color de fondo del visualizador debe persistir de forma determinista entre reinicios del kernel y recargas del visor.
2. Los mensajes generados por `_build_export_messages()` deben incluir la instrucción precisa para restablecer el color de fondo de la escena configurado por el usuario.
3. Se debe incorporar una prueba unitaria de regresión que verifique que, tras cambiar el color de fondo de la escena y exportar los mensajes de reconstrucción, el comando `"set_background_color"` con el valor de color correcto se encuentra presente en la lista de exportación.
