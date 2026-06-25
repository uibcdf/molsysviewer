# Propuesta de Mejora: Mitigación de Saturación por Eventos de Alta Frecuencia (Throttling & Debouncing)

## 1. Contexto y Diagnóstico

MolSysViewer expone eventos interactivos del lienzo (tales como cambios de cámara `"viewer:camera-moved"`, eventos de cruce de cursor `"viewer:hover-changed"`, etc.) a través de dos canales:
1. **Bus de Eventos Local (Frontend)**: Latencia cero (< 1 ms), ideal para paneles y widgets de JavaScript.
2. **Callbacks de Python**: El usuario puede registrar funciones en el kernel de Jupyter usando `view.on_hover(callback)` o `view.on_camera_moved(callback)`.

El problema de rendimiento surge porque **el movimiento de la cámara o el cruce continuo del cursor del ratón sobre la proteína genera cientos de eventos por segundo en el navegador**. En la arquitectura actual, cada uno de estos eventos genera un mensaje JSON asíncrono que viaja a través del canal de comunicación (websocket de AnyWidget) hacia el kernel de Python en el servidor.

Al no existir un mecanismo de limitación de frecuencia de emisión (**throttling**) ni de agrupación (**debouncing**) en el frontend para el envío de mensajes de red, el canal de comunicación se satura rápidamente de mensajes repetitivos de coordenadas de cámara o identificadores de átomos hover.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Retraso Acumulativo en Jupyter (Lag)**: La cola de mensajes del kernel de Jupyter se inunda. Cuando el usuario intenta ejecutar otra celda de código en Python o interactuar con un slider, la acción experimenta un retraso severo (lag) de varios segundos mientras el kernel procesa la larga fila de eventos de cámara acumulados.
2. **Congelamiento Temporal del Cuaderno**: En entornos con conexiones de red lentas o con kernels muy cargados, la avalancha de mensajes de AnyWidget puede provocar la pérdida de conexión o el congelamiento temporal de la sesión del notebook de Jupyter.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Implementación de Throttling y Debouncing Selectivos en el Frontend

Se propone estructurar la emisión de eventos desde JavaScript (`viewer-controller.ts`) hacia el backend de Python aplicando técnicas de control de flujo en caliente:

1. **Throttling en Eventos Continuos (Movimiento de Cámara)**:
   * **Mecanismo**: Limitar la frecuencia con la que el evento de movimiento de cámara se transmite a Python. En lugar de enviar un mensaje en cada frame de renderizado (60 FPS), aplicar un *throttle* de 100 ms o 200 ms.
   * **Implementación**: El frontend acumula las actualizaciones de cámara y envía un único mensaje representativo como máximo cada 150 ms durante el movimiento continuo, enviando el mensaje final preciso inmediatamente después de que el movimiento se detenga (*debounced tail*).
   * **Pros**: Reduce el tráfico de red de eventos de cámara en más de un 80%, garantizando fluidez total en el kernel de Jupyter.

2. **Debouncing en Eventos Rápidos (Hover de Átomos)**:
   * **Mecanismo**: Cuando el usuario pasa el cursor rápidamente sobre una hélice alfa, se cruzan decenas de átomos en milisegundos. Aplicar un *debounce* de 50 ms a 80 ms antes de notificar un evento de hover a Python.
   * **Implementación**: Si el cursor pasa de un átomo a otro en menos de 50 ms, el frontend cancela la notificación del átomo anterior y solo envía el mensaje de hover para el átomo en el que el cursor se detiene finalmente por más de 50 ms.
   * **Pros**: Evita enviar ráfagas de mensajes inútiles para átomos cruzados de paso rápido, enviando solo interacciones de inspección intencionales.

---

## 4. Criterios de Aceptación

1. Las suscripciones locales en JavaScript (Add-ons en el frontend) deben seguir recibiendo eventos locales a la máxima frecuencia posible (latencia < 1 ms) para mantener la interactividad a 60 FPS en el navegador.
2. La transmisión de mensajes de eventos continuos (hover, cámara) hacia el kernel de Python a través de AnyWidget debe estar estrictamente limitada mediante técnicas de throttling y debouncing en el frontend de JavaScript.
3. El movimiento continuo de la cámara en 3D durante 10 segundos no debe inyectar más de 70 mensajes en el canal de comunicación de AnyWidget, eliminando cualquier retraso acumulativo (lag) en la ejecución de celdas del notebook de Jupyter.
