# Propuesta de Mejora: Robustez en Comunicación Qt-WebEngine (Evitar Bloqueos y Pérdida de Mensajes)

## 1. Contexto y Diagnóstico

El prototipo de visor de escritorio autónomo (`standalone_qt0`) utiliza PySide6 (específicamente la versión personalizada `PySide6_uibcdf`) para renderizar el visor molecular en una ventana nativa mediante `QWebEngineView`.

En `molsysviewer/standalone_qt/utils.py`, la comunicación desde la interfaz de Python de la aplicación nativa de Qt hacia el visor web embebido se realiza a través de llamadas asíncronas a JavaScript utilizando `runJavaScript`:
```python
def _send_viewer_message(webview, message: dict[str, Any]) -> None:
    page = webview.page() if hasattr(webview, "page") else None
    if page is None or not hasattr(page, "runJavaScript"):
        return
    payload = json.dumps(message, separators=(",", ":"))
    script = (
        "if (window.__molsysviewerDocsHandleMessage) { "
        f"window.__molsysviewerDocsHandleMessage({payload}); "
        "}"
    )
    page.runJavaScript(script)
```

Existen dos vulnerabilidades críticas de diseño e integración en este mecanismo:
1. **Pérdida Silenciosa de Mensajes en Inicialización**: Python carga la página del visor mediante `webview.setUrl(QUrl.fromLocalFile(html_path))` y, casi de inmediato o durante eventos de carga rápida, intenta enviar mensajes de configuración o carga estructural. Si el visor web no ha terminado de cargarse e inicializar el objeto `window.__molsysviewerDocsHandleMessage`, la condición `if` en el script inyectado evalúa a falso y el mensaje se descarta silenciosamente.
2. **Riesgo de Deadlock en Hilos / Bucle de Eventos**: `QWebEngineView` ejecuta el motor Chromium en un proceso del sistema operativo independiente de Python. La comunicación se realiza mediante IPC (Inter-Process Communication). Si el backend de Python inunda la vista con llamadas de renderizado rápidas (ej. actualizaciones constantes de coordenadas de trayectorias) o si bloquea el bucle de eventos principal de Qt esperando de forma síncrona una respuesta del frontend, se produce un deadlock (congelamiento total de la interfaz gráfica y del kernel de Python).

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Interfaz Congelada (Cuelgues en Escritorio)**: Al cargar sistemas moleculares grandes o trayectorias conformacionales densas en el visor Qt autónomo, la aplicación nativa se congela frecuentemente y el sistema operativo muestra el diálogo de "La aplicación no responde".
* **Desincronización del Visor**: Estructuras moleculares, anotaciones o mediciones iniciales se pierden durante la carga de la aplicación debido a que los primeros mensajes de configuración se envían antes de que el motor de JavaScript del navegador esté listo.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta 1: Implementación de un Protocolo de Handshake (Apretón de Manos)
Establecer un canal de comunicación bidireccional formal utilizando la infraestructura de `QWebChannel` nativa de Qt, garantizando que el backend de Python no envíe mensajes hasta que el frontend declare explícitamente estar listo:

1. **Declaración de Readiness del Frontend**:
   El visor web en HTML/JS, una vez inicializado Mol* y registrados sus manejadores globales, emite un evento o señal nativa hacia el host Python a través de `QWebChannel`: `"molsysviewer_ready"`.
2. **Cola de Mensajes en Backend**:
   El backend de Python retiene todos los mensajes en una cola de pre-carga (`_pending_messages`). Una vez recibido el handshake `"molsysviewer_ready"`, Python libera y procesa secuencialmente la cola de mensajes acumulados.

### Propuesta 2: Comunicación Basada en Colas Asíncronas No Bloqueantes
Evitar inundar el canal IPC mediante el uso de un limitador de frecuencia (throttling o debouncing) en Python antes de despachar mensajes hacia `runJavaScript`, garantizando que la cola de eventos del bucle de Qt nativo tenga tiempo para procesar los frames intermedios y de repintado del motor gráfico.

---

## 4. Criterios de Aceptación

1. El visor de escritorio autónomo no debe perder ningún mensaje de configuración ni estructura cargada al iniciar la aplicación, independientemente del tiempo que tarde la página HTML en renderizarse e inicializar JavaScript.
2. La carga repetitiva de archivos moleculares y la reproducción de trayectorias en la aplicación nativa de Qt no debe provocar congelamientos de la GUI ni bloqueos del hilo principal de ejecución.
3. Se deben definir pruebas automatizadas de robustez (o un script de simulación de estrés en `sandbox/`) que envíe cientos de comandos de actualización secuenciales al visor Qt y convalide que la aplicación finaliza la secuencia de manera exitosa y mantiene la capacidad de respuesta.
