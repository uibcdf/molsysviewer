# Propuesta de Mejora: Optimización de Tráfico de Red en Jupyter (Eliminación de Redundancia de viewer.js)

## 1. Contexto y Diagnóstico

MolSysViewer se integra en entornos Jupyter Notebook y JupyterLab a través de la librería `anywidget`. En `molsysviewer/widget.py`, la clase `MolSysViewerWidget` define los traitlets sincronizados entre Python y el frontend.

El problema radica en la forma en que se implementa la duplicación del visor en ventanas emergentes (popups):
```python
class MolSysViewerWidget(anywidget.AnyWidget):
    _esm = (Path(__file__).parent / "viewer.js").read_text(encoding="utf-8")
    
    # Send the viewer source code to the frontend so it can replicate itself in the popup
    # regardless of server configuration, ports, or CDNs.
    popup_js_source = T.Unicode(_esm).tag(sync=True)
```

El archivo `viewer.js` es un artefacto compilado que pesa aproximadamente **5.8 MB**. Al definir `popup_js_source` como un traitlet sincronizado (`tag(sync=True)`), Jupyter serializa y transmite este contenido completo de 5.8 MB a través del WebSocket **para cada instancia del widget que se cree en el notebook**.

Si un usuario abre un notebook y genera 5 celdas con visores independientes, la infraestructura de Jupyter transmitirá **29 MB** de datos JSON redundantes por la red. Si abre 10 celdas, serán **58 MB**. En entornos locales esto genera una latencia perceptible al renderizar nuevas celdas, pero en conexiones remotas (JupyterHub corporativo, Google Colab, Binder o túneles SSH con reenvío de puertos), este comportamiento causa regularmente desbordamientos del búfer del WebSocket, desconexiones del kernel de Jupyter, congelamientos del navegador y fallos en la persistencia de la sesión.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Inestabilidad del Kernel**: La transmisión masiva de buffers de texto de 5.8 MB satura el canal de control y datos de Jupyter. Esto provoca desconexiones aleatorias del kernel de Python durante sesiones de análisis interactivo de trayectorias.
* **Degradación del Rendimiento en Redes Remotas**: Investigadores que trabajan en infraestructuras en la nube experimentan retrasos severos (de varios segundos a minutos) al instanciar visores moleculares, dañando la fluidez del análisis visual.
* **Consumo Ineficiente de Memoria**: Tanto el proceso de Python como el proceso del navegador del cliente deben almacenar y procesar copias redundantes de la cadena de caracteres de 5.8 MB por cada celda activa.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Alternativa A: Extracción Local del Código en el Frontend (Recomendada)
Dado que el navegador ya ha descargado y ejecutado `viewer.js` para inicializar el módulo ESM del widget, el frontend puede auto-replicarse leyendo su propia fuente o extrayéndola de los módulos cargados en el documento, evitando transmitirla desde Python.

### Alternativa B: Carga Bajo Demanda mediante Mensajes Personalizados
En lugar de un traitlet sincronizado incondicionalmente al instanciar el widget, se propone enviar el código únicamente cuando el usuario haga clic explícito en el botón de "popout" (ventana emergente).
1. El usuario hace clic en "popout" en la UI.
2. El frontend envía un mensaje personalizado al backend: `{"type": "request_popup_source"}`.
3. El backend responde con un mensaje único que contiene el código.
Esto reduce el tráfico de inicialización a **0 MB** para el 95% de los casos de uso cotidianos donde no se requiere la ventana emergente.

### Alternativa C: Exposición a través de una Ruta Estática de Jupyter
Registrar un manejador de contenido o servidor de archivos estáticos en el servidor de Jupyter para que el frontend del popup pueda cargar el script directamente a través de una petición HTTP estándar (`<script src="/static/molsysviewer/viewer.js">`), beneficiándose del almacenamiento en caché nativo del navegador.

---

## 4. Criterios de Aceptación

1. La instanciación de un nuevo `MolSysViewerWidget` no debe transmitir los 5.8 MB de `viewer.js` de manera incondicional a través del WebSocket de Jupyter. El tamaño del estado inicial sincronizado debe ser menor a 50 KB (excluyendo la topología molecular de la simulación).
2. La funcionalidad de ventana emergente ("popout") debe seguir operando de forma transparente en entornos locales y remotos (JupyterHub, Colab), obteniendo el código ESM bajo demanda o mediante caché local.
3. Se deben realizar pruebas de perfilado de tráfico de red en Jupyter para verificar que la creación de múltiples celdas consecutivas no incrementa linealmente el tráfico del WebSocket en múltiplos de 5.8 MB.
