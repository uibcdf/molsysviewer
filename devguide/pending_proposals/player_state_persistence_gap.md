# Propuesta de Mejora: Persistencia y Reproducción del Estado Activo del Reproductor (Player State)

## 1. Contexto y Diagnóstico

MolSysViewer proporciona el gestor `PlayerManager` (`molsysviewer/player.py`) para controlar la navegación y reproducción de trayectorias moleculares. El usuario puede modificar el comportamiento del reproductor configurando parámetros dinámicos como los cuadros por segundo (`fps`), el tamaño de paso (`step_size`), el modo de reproducción (`"loop"`, `"once"`, `"ping-pong"`) y la dirección de avance (`"forward"`, `"backward"`).

El problema de reproducibilidad radica en que **el estado de reproducción del player no se captura en el historial de mensajes de exportación**. Cuando se invoca a `_build_export_messages()` en `molsysviewer/viewer/core.py` para serializar la escena:
1. El historial de mensajes contiene los comandos para regenerar la geometría y la cámara.
2. Sin embargo, **los parámetros de reproducción del player configurados por el usuario y el estado activo de reproducción (`is_playing`) se omiten del historial**.
3. Al reconstruir el visor a partir de los mensajes exportados (por ejemplo, en un reporte HTML estático interactivo o tras una recarga del kernel), el reproductor se inicializa siempre en estado pausado con los parámetros por defecto de 30 FPS y modo loop, perdiendo la configuración personalizada de la animación.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Pérdida del Contexto de Animación**: Si un investigador configura una animación de dinámica molecular para que se reproduzca a una velocidad lenta específica (ej. 5 FPS en modo ping-pong) para ilustrar un cambio conformacional sutil en una presentación o reporte interactivo, otros usuarios que abran la sesión exportada verán la animación correr a la velocidad rápida por defecto de 30 FPS, perdiendo el foco y la intención del autor original.
* **Falta de Automatización en Presentaciones**: No es posible exportar una vista que comience a reproducir automáticamente la animación al ser cargada, obligando al espectador final a buscar y hacer clic manualmente en el botón de reproducción en el panel de control.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Serialización del Estado Dinámico del Player en el Replay de la Escena

Se propone integrar el estado de reproducción en la historia de replay del visor:

1. **Almacenar la Configuración del Player**:
   Añadir un diccionario de estado de reproducción en `core.py` (ej. `self._player_settings: dict[str, Any]`) que almacene de forma centralizada las propiedades del reproductor: `fps`, `step_size`, `mode`, `direction` e `is_playing`.
   
2. **Interceptar y Registrar Operaciones**:
   Cuando el usuario llame a métodos mutadores en `player.py` (como `play`, `set_fps`, `set_mode`, etc.), actualizar el diccionario en el backend y registrar el comando en la colección de historia de replay:
   ```python
   def play(self, fps=None, mode=None, direction=None, step_size=None, *, skip_digestion=False) -> None:
       # ...
       # Actualizar el diccionario local
       self._player_settings.update({
           "is_playing": True,
           "fps": self._fps,
           "mode": self._mode,
           "direction": self._direction,
           "step": self._step_size
       })
   ```

3. **Serializar en el Replay de Exportación**:
   Modificar `_build_export_messages()` en `core.py` para que lea el diccionario `_player_settings` y anexe los mensajes de configuración del reproductor (como `"set_trajectory_playback"`) al final de la lista de exportación, garantizando que el visor se configure con el estado de animación preciso del autor.

---

## 4. Criterios de Aceptación

1. La configuración personalizada del reproductor de trayectoria (`fps`, `step_size`, `mode`, `direction`) debe persistir de forma determinista entre reinicios del kernel y recargas del visor.
2. Los mensajes generados por `_build_export_messages()` deben incluir las instrucciones precisas para restablecer el estado de reproducción y los parámetros del player.
3. Se debe incorporar una prueba de regresión que verifique que, tras configurar el reproductor a 10 FPS en modo ping-pong y exportar el estado, las opciones correspondientes a `"set_trajectory_playback"` con los valores de FPS y modo correctos se encuentran en la lista de mensajes de replay.
