# Propuesta de Mejora: Protocolo de Confirmación y Propagación de Errores (Error Acknowledgment)

## 1. Contexto y Diagnóstico

MolSysViewer coordina acciones iniciadas por el usuario en el lienzo 3D o en el menú de contexto (tales como `"toggle_region_visibility"`, `"delete_region"`, `"remove_selection"`, etc.) enviando mensajes asíncronos desde JavaScript hacia el despachador de eventos `_handle_frontend_event` en `molsysviewer/viewer/core.py`.

El problema de robustez radica en que:
1. El despachador de Python realiza validaciones estrictas sobre estos mensajes (ej. verificar la existencia de tags de regiones o selecciones) y lanza excepciones estándar en Python (`ValueError`, `KeyError`) ante fallos.
2. En la arquitectura actual de comunicación asíncrona de Jupyter/AnyWidget, estas excepciones interrumpen el hilo de procesamiento del mensaje en el kernel de Python. Se registran en el stderr de la terminal del kernel o en los logs del servidor de Jupyter.
3. **El frontend de JavaScript nunca se entera de que la operación en Python falló**. No existe un canal de respuesta para notificar errores de procesamiento de intenciones de vuelta al navegador.

---

## 2. Impacto Científico y de Experiencia de Usuario

La ausencia de un mecanismo de propagación de excepciones genera las siguientes fallas:
* **Desfase Silencioso de la Aplicación**: La interfaz de usuario en el navegador (el lienzo 3D de Mol* o los paneles reactivos) asume que la acción en el backend se completó con éxito. El usuario ve un estado visual en pantalla que ya no coincide con el estado lógico real del kernel de Python (por ejemplo, una región que visualmente se elimina pero que lógicamente sigue existiendo y operando en las variables del kernel).
* **Falta de Diagnóstico para el Usuario**: Cuando una acción interactiva falla (ej. intentar guardar una selección vacía o renombrar una región con un nombre duplicado), la interfaz no presenta ninguna alerta ni advertencia visual, dejando al usuario confundido sobre por qué la herramienta no responde o se comporta de forma errática.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Introducción de un Canal de Respuesta de Confirmación de Errores (`error_ack`)

Se propone reestructurar la gestión de excepciones en el despachador `_handle_frontend_event` de Python e introducir un protocolo de notificación de errores:

1. **Captura Global de Excepciones en el Despachador**:
   Envolver la ejecución de intenciones en `_handle_frontend_event` en un bloque `try-except` general:
   ```python
   def _handle_frontend_event(self, content: Mapping[str, Any]) -> None:
       event = content.get("event")
       # ...
       try:
           if event == "interaction_context_action":
               self._process_context_action(content)
       except Exception as e:
           # Enviar notificación de error de vuelta al frontend
           self._send_runtime_only({
               "op": "backend_error_occurred",
               "trigger_event": event,
               "action": content.get("action"),
               "error_type": type(e).__name__,
               "error_message": str(e)
           })
           # Opcional: registrar el log en Python de forma controlada sin romper el hilo
           logger.error(f"Error processing frontend event {event}: {e}", exc_info=True)
   ```

2. **Interceptación y Alertas en el Frontend (JavaScript)**:
   En `viewer-controller.ts`, registrar un receptor para el mensaje `"backend_error_occurred"`. Al recibirlo, la interfaz de usuario debe:
   * Revertir el estado visual local si corresponde (por ejemplo, volver a mostrar el botón de la región si su borrado en Python falló).
   * Presentar una notificación o alerta visual no obstructiva en el lienzo (ej. usando un banner de error temporal de Mol* o un overlay de notificación del panel lateral) informando el mensaje de error científico al usuario.

---

## 4. Criterios de Aceptación

1. Ninguna excepción de Python lanzada durante el procesamiento de eventos interactivos provenientes del frontend debe abortar silenciosamente el canal de AnyWidget sin notificar al navegador.
2. Ante un fallo en el backend de Python, la interfaz de JavaScript de MolSysViewer debe recibir el mensaje de error y notificar visualmente al usuario en la pantalla con el tipo de error y su descripción.
3. Se debe incluir una prueba automatizada en Python que simule un mensaje interactivo erróneo (ej. borrar una región inexistente) y verifique que la vista responde enviando un mensaje del tipo `"backend_error_occurred"` al frontend.
