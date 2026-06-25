# Propuesta de Mejora: Sincronización Bidireccional del Reproductor de Trayectorias

## 1. Contexto y Diagnóstico

En MolSysViewer, la animación de trayectorias es asíncrona por diseño. Cuando el usuario ejecuta `view.player.play()` en Python, el backend envía un mensaje unidireccional `"op": "set_trajectory_playback", "action": "play"` al frontend, delegando la reproducción nativa a 30 FPS al motor de renderizado Mol* en el hilo del navegador.

El problema radica en que **el frontend de JavaScript no emite notificaciones periódicas de actualización de frame hacia el backend de Python durante la reproducción**. Como resultado:
* La propiedad `view.player.index` (definida en `molsysviewer/player.py` como lectura del atributo privado `self._view._current_structure_index`) permanece estática en el valor que tenía antes de reproducir, o en el último valor fijado explícitamente mediante `go_to_structure`.
* El estado lógico del reproductor en Python está completamente desfasado del estado visual real que observa el usuario en el navegador.

---

## 2. Impacto Científico y de Experiencia de Usuario

La falta de sincronización bidireccional en el frame activo tiene las siguientes implicaciones:
1. **Fallas en Add-ons Reactivos**: Si un panel lateral de un add-on en Jupyter (por ejemplo, un calculador de distancias interactivo) intenta consultar el frame activo a través de `view.player.index` durante la animación para actualizar una gráfica 2D reactiva, obtendrá datos obsoletos.
2. **Inconsistencia de Análisis**: Si el usuario detiene la animación en el navegador (usando la interfaz visual de Mol* o el scrubber) y luego ejecuta una celda de análisis en Python asumiendo que opera sobre el frame visible en pantalla, el kernel calculará propiedades basándose en el frame estático desactualizado.
3. **Pérdida de Reproducibilidad**: El estado del visor capturado en Python no representará fielmente lo que el usuario observaba en la pantalla al momento de guardar el estado o exportar la sesión.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Alternativa A: Emisión de Eventos de Frame de Alta Frecuencia (Pulsos)
* **Descripción**: Modificar el bucle de reproducción en el frontend de JavaScript para que emita un mensaje de evento `"trajectory_frame_changed"` a Python cada vez que el frame cambie.
* **Pros**: Sincronización de frame perfecta en tiempo real en Python.
* **Contras**: Inundación de mensajes a través del canal de AnyWidget (30 mensajes por segundo), lo que puede saturar el kernel de Jupyter y degradar drásticamente el rendimiento de la sesión.

### Alternativa B: Notificación de Frame con Throttling/Debouncing (Recomendada)
* **Descripción**: El frontend emite notificaciones de cambio de frame hacia Python solo bajo las siguientes condiciones:
  1. Cuando la reproducción se pausa o se detiene (`action: "stop"`), enviando el frame final de parada de forma síncrona.
  2. Durante la reproducción activa, emitir actualizaciones a una frecuencia significativamente menor (ej. máximo 3 o 5 actualizaciones por segundo usando *throttling*), actualizando el valor de `_current_structure_index` en Python de forma asíncrona.
* **Pros**: Mantiene el kernel de Python relativamente actualizado con una carga de red despreciable, y garantiza consistencia absoluta al pausar o detener.
* **Contras**: Ligero retraso (máximo 200 ms) en el valor de `view.player.index` en Python durante la reproducción activa.

---

## 4. Criterios de Aceptación

1. La propiedad de lectura `view.player.index` en Python debe reflejar con precisión el frame en el que la animación se detuvo o pausó en la interfaz del navegador.
2. Durante la reproducción activa a 30 FPS, `view.player.index` debe actualizarse asíncronamente en Python a una tasa moderada sin causar saturación ni retrasos en la cola de mensajes de AnyWidget.
3. Se debe incluir una prueba de integración (o regresión de simulación de mensajes) que verifique que el mensaje de cambio de frame enviado desde el frontend actualiza correctamente el atributo `_current_structure_index` en el backend.
