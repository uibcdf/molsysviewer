# Propuesta de Mejora: Recuperación Automática y Resiliencia ante Pérdida de Contexto WebGL

## 1. Contexto y Diagnóstico

MolSysViewer corre sobre Mol* en el frontend, motor gráfico que utiliza WebGL/WebGPU para el renderizado acelerado por hardware de estructuras tridimensionales en el navegador del usuario.

El problema de robustez radica en que **los navegadores web pueden perder de forma repentina e impredecible el contexto WebGL (GPU Crash)**. La pérdida de contexto (disparada por el evento del navegador `webglcontextlost`) ocurre frecuentemente bajo las siguientes condiciones:
* Cuando el ordenador entra en suspensión o hibernación y se reactiva.
* Cuando la GPU se sobrecarga con otras tareas del sistema.
* Cuando el usuario tiene múltiples pestañas con visores tridimensionales pesados abiertos en el navegador simultáneamente.
* Cuando los controladores de video del sistema operativo se reinician de forma automática.

Cuando ocurre una pérdida de contexto WebGL:
1. El lienzo de renderizado de MolSysViewer queda permanentemente congelado o se vuelve completamente negro.
2. **El backend de Python no recibe ninguna notificación del fallo**, por lo que sigue enviando comandos de visualización y modificando variables con aparente éxito (`_send` no reporta errores).
3. El usuario se encuentra frente a un visualizador "muerto" y congelado, perdiendo el trabajo de la sesión interactiva a menos que recargue la pestaña del navegador o reinicie por completo la celda del notebook.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Pérdida de Interactividad e Información**: Los científicos que realizan análisis finos de trayectorias largas pierden sus anotaciones y mediciones interactivas si la GPU colapsa, obligándolos a repetir los pasos de exploración desde cero.
* **Degradación en Demostraciones en Vivo**: Los fallos silenciosos del lienzo WebGL durante presentaciones científicas o clases en vivo dañan la experiencia de usuario y la percepción de robustez de la herramienta.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Manejador de Pérdida de Contexto y Auto-recuperación por Replay

Se propone dotar al frontend y backend de MolSysViewer de resiliencia ante fallos de GPU:

1. **Interceptar el Evento en JavaScript**:
   Registrar un oyente para el evento de pérdida de contexto en el canvas de Mol*:
   ```typescript
   canvas.addEventListener('webglcontextlost', (event) => {
       event.preventDefault(); // Permitir la restauración del contexto
       this.handleWebGLContextLoss();
   }, false);
   ```

2. **Notificar a Python y Presentar Alerta Visual**:
   * Al perder el contexto, el frontend envía un mensaje `"op": "webgl_context_lost"` a Python.
   * La UI del visor muestra un overlay de advertencia descriptivo: *"Conexión con la GPU perdida. Intentando restaurar la escena..."*
   * Python registra el log de diagnóstico correspondiente en el kernel de Jupyter.

3. **Restauración y Auto-recuperación por Replay**:
   * Escuchar el evento de restauración del navegador:
     ```typescript
     canvas.addEventListener('webglcontextrestored', () => {
         this.recoverWebGLContext();
     }, false);
     ```
   * Una vez restaurado el contexto por el navegador, el frontend notifica a Python con `"op": "webgl_context_restored"`.
   * El backend de Python, al recibir la confirmación de restauración, **re-inyecta de forma automatizada toda la historia de replay de la escena** (`_build_export_messages()`), restaurando de forma idéntica las mallas de shapes, las anotaciones, las mediciones y la cámara. El visor se recupera automáticamente en menos de un segundo, sin intervención del usuario.

---

## 4. Criterios de Aceptación

1. La pérdida de contexto WebGL en el navegador no debe dejar el lienzo del visor congelado en negro de forma indefinida y silenciosa.
2. El visualizador debe alertar al usuario en pantalla sobre el colapso de la GPU y reintentar la conexión de forma proactiva.
3. Al restaurarse el contexto WebGL por el navegador, MolSysViewer debe autorecuperarse de forma transparente y reconstruir la escena molecular completa a partir de la historia de replay almacenada en Python, devolviendo el visor al estado exacto previo al fallo.
