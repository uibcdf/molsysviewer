# Propuesta de Mejora: Sincronización Síncrona de Rebuild en Visor Standalone (Qt WebEngine)

## 1. Contexto y Diagnóstico

MolSysViewer soporta un entorno standalone fuera de Jupyter basado en **PyQt/PySide (Qt WebEngine)** y canales de comunicación locales (`molsysviewer/standalone.py` y `molsysviewer/viewer/movie.py`). Este entorno permite la visualización offline de estructuras y la exportación de trayectorias en imágenes de alta resolución sin necesidad de un servidor de cuadernos activo.

El problema de robustez radica en la **fase de reconstrucción dinámica de la vista (Rebuild)**. Cuando la topología molecular en Python se altera y se invoca a `view._rebuild_view_from_current_molsys()`, el backend limpia el lienzo y envía una secuencia de bloques de carga pesados (coordenadas, topología, estados de capas, shapes e historial de reproducción) de forma consecutiva.

En Jupyter, AnyWidget maneja esto mediante una cola de mensajes en el websocket. Sin embargo, en el canal local de Qt WebEngine:
1. Los mensajes viajan a través de scripts inyectados y canales de comunicación asíncronos nativos de Qt (`QWebChannel`).
2. Si el volumen de datos es muy grande, la inyección sucesiva de mensajes de carga de topología pesada puede saturar el buffer de Qt WebEngine antes de que el frontend de JavaScript termine de procesar el bloque anterior.
3. Al no existir un **semáforo síncrono o protocolo de handshake** en el canal local de Qt para confirmar que el bloque de inicialización fue procesado con éxito, el visualizador puede congelarse permanentemente en una pantalla blanca de carga indefinida (*white-screen freeze*).

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Inestabilidad del Entorno Standalone**: El entorno de escritorio (esencial para la automatización de renderizado de películas y análisis masivos fuera del navegador) se vuelve propenso a fallos catastróficos y bloqueos silenciosos al procesar sistemas moleculares de tamaño intermedio a grande.
2. **Pérdida de Tiempo de Cómputo**: Las tareas de exportación de trayectorias complejas (ej. renderizar 500 frames) que se ejecutan de forma automatizada se abortan a mitad del proceso si el canal de Qt se satura, haciendo que los scripts de línea de comandos fallen de forma no reproducible.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Implementación de una Cola Transaccional con Confirmación Activa (`Handshake Rebuild`)

Se propone rediseñar el canal de comunicación del visor standalone para implementar un flujo transaccional controlado:

1. **Protocolo de Handshake para Carga de Bloques**:
   En lugar de inyectar toda la secuencia de mensajes de reconstrucción de forma asíncrona y descontrolada, Python debe pausar el envío tras enviar el bloque de topología molecular y esperar una confirmación explícita del frontend (`"op": "rebuild_topology_ack"`).
   
2. **Cola de Transacciones en el Canal de Qt**:
   Implementar un semáforo síncrono en `standalone.py` que controle la tasa de transferencia de datos:
   ```python
   def _send_standalone_message(self, msg: dict) -> None:
       # Si es un mensaje de reconstrucción pesado, encolarlo y esperar la confirmación del anterior
       if msg.get("op") == "load_topology" and not self._frontend_ready_for_data:
           self._pending_standalone_queue.append(msg)
           return
       # Enviar mensaje a través del canal de Qt WebEngine
       self._qt_webchannel.inject_script(...)
   ```

3. **Monitoreo de Liveness (Heartbeat)**:
   Si el frontend no responde con un ack de confirmación en un tiempo prudencial (ej. 2.0 segundos durante la carga), el backend en Python debe reintentar el envío o abortar de forma controlada lanzando una excepción informativa (`RuntimeError`), en lugar de permitir el congelamiento silencioso del proceso de escritorio.

---

## 4. Criterios de Aceptación

1. La reconstrucción del visor en entornos standalone (Qt WebEngine) no debe provocar congelamientos de pantalla blanca ni bloqueos indefinidos del hilo de la interfaz gráfica al procesar macromoléculas complejas.
2. El flujo de mensajes de inicialización y reconstrucción pesados debe estar regulado por confirmaciones de recepción activas (`handshake`) entre el canal de Qt de Python y JavaScript.
3. Se debe incluir una prueba de estrés automatizada en el entorno standalone que realice múltiples reconstrucciones dinámicas sucesivas y verifique que la comunicación se mantiene activa y libre de bloqueos.
