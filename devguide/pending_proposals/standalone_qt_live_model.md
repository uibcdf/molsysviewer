# Propuesta: migrar standalone Qt al modelo vivo de mensajes

## Estado

Parcialmente implementada.

Implementado hasta ahora:

- transporte JS -> Python por esquema URL en `bootDocsView()`;
- eventos `ready`, `message_ack`, `message_error`, `structure_ready` y
  `render_ready`;
- `QtMessageBridge` runtime-only con cola, IDs, generation, ack/error, timeout y
  coalescing inicial;
- shell Qt persistente sin payload molecular inicial embebido;
- cargas normales de demo/fichero/PDB/source por mensajes vivos;
- `load_molsys_payload_ref` para payloads grandes, con umbral configurable y
  limpieza de archivos temporales al recibir ack/error/timeout;
- configuración defensiva de rutas Qt WebEngine en layouts conda split
  (`libexec`, `resources`, `translations/qtwebengine_locales`);
- export HTML separado, reconstruido desde el sistema cargado, no copiando la
  shell Qt;
- tests unitarios con fakes Qt para el bridge y el flujo standalone;
- **registro de los esquemas URL custom** (`molsysviewer` para eventos,
  `molsysviewer-payload` para datos) con `QWebEngineUrlScheme.registerScheme`
  antes de crear la `QApplication` — sin esto Chromium trata el esquema como
  inválido y `acceptNavigationRequest` puede no dispararse (canal JS->Python);
- **payloads grandes servidos por `QWebEngineUrlSchemeHandler`** en memoria sobre
  `molsysviewer-payload://payload/<id>`, en vez de archivo temporal +
  `fetch(file://...)` (que Chromium bloquea desde una página `file://`). Elimina
  el flag inseguro `LocalContentCanAccessFileUrls` y los temporales;
- **primitiva de espera cooperativa** para export de películas: el bucle bombea
  `view._qt_process_events` (que el host Qt fijaría a
  `QCoreApplication.processEvents`) si existe; en Jupyter/no-Qt degrada al sleep.

Pendiente (bloqueado por entorno / fase posterior):

- **validación con ventana Qt real** de todo el round-trip (que el esquema de
  eventos dispare `acceptNavigationRequest`, que el `fetch` del esquema de
  payload funcione, que las cargas no hagan timeout). Existe el arnés:
  `test_qt_live_model_smoke_real_window` (marcado `skip`);
- desbloquear el entorno: `icudtl.dat`/packaging `qt6-webengine-uibcdf`, sin lo
  cual no se puede validar nada de lo anterior;
- **fase 4/5**: que el host Qt fije `_qt_process_events` y **enrute los eventos
  `movie_frame`/`movie_export_done` al `view`** (hoy el bridge solo procesa
  ack/error/ready; la primitiva de espera existe pero aún no tiene consumidor);
- refinamiento de status/progress visual durante cargas largas;
- decidir qué estado UI se preserva o resetea por generación.

Esta propuesta sustituye y consolida las propuestas previas sobre pérdida de
mensajes en `QWebEngineView` y congelamientos durante rebuilds Qt. El objetivo
no es sólo añadir retries al canal actual, sino migrar `standalone_qt0` desde el
modelo interno de HTML estático hacia un modelo vivo de mensajes equivalente en
concepto al de AnyWidget/Jupyter.

## Motivación

`standalone_qt0` debe comportarse como una aplicación de escritorio interactiva,
no como una vista HTML regenerada en cada carga. El flujo actual genera un HTML
nuevo con mensajes embebidos y recarga `QWebEngineView` con `setUrl(...)` cuando
se carga un demo, fichero, PDB ID o fuente MolSysMT. Este modelo es simple y
exportable, pero destruye el runtime del frontend en cada rebuild.

Consecuencias del modelo actual:

- Parpadeo visible al recargar la página.
- Reinicialización completa de Chromium, el bundle de MolSysViewer, Mol* y el
  contexto WebGL.
- Pérdida de estado visual de la UI, como panel activo, scroll, foco o estado
  local de workbench/add-ons.
- Duplicación arquitectónica: Jupyter usa mensajes vivos; Qt usa HTML estático
  para cargas grandes y `runJavaScript` fire-and-forget para comandos pequeños.
- Imposibilidad práctica de que add-ons como TopoMT o ElasNetMT actualicen la
  escena 3D y la UI de trabajo de forma fluida sin recargar toda la aplicación.

Para que Qt sea una superficie de producto seria en 1.0, el HTML estático debe
dejar de ser el mecanismo interno de renderizado. Debe conservarse como modo de
exportación reproducible, no como transporte principal de la app Qt.

## Diagnóstico validado

El código actual confirma estas observaciones:

- `molsysviewer/standalone_qt/application.py` crea un `QWebEngineView` y carga un
  HTML generado con `webview.setUrl(QUrl.fromLocalFile(html_path))`.
- `molsysviewer/standalone_qt/utils.py::_rebuild_qt_html()` regenera HTML
  estático mediante `build_standalone0_html(..., mode="lite", ...)`.
- Las acciones de carga Qt reconstruyen ese HTML y recargan la página.
- `molsysviewer/standalone_qt/utils.py::_send_viewer_message()` inyecta JS con
  `runJavaScript` y descarta silenciosamente el mensaje si
  `window.__molsysviewerDocsHandleMessage` aún no existe.
- `bootDocsView()` en `js/src/index.ts` instala
  `window.__molsysviewerDocsHandleMessage` y procesa los mensajes iniciales en
  orden, pero en modo lite/Qt no existe un canal host robusto para notificar
  readiness, ack o errores a Python.
- El camino AnyWidget sí tiene evento `ready`, `initial_messages` y cola de
  mensajes iniciales; Qt no tiene una política equivalente.
- El mensaje existente para cambiar de frame es `set_trajectory_frame`, no
  `set_structure_index`.
- `viewer/movie.py` contiene esperas con `time.sleep(...)`; en contexto Qt esas
  esperas pueden impedir que el hilo principal procese eventos necesarios para
  recibir respuestas del frontend.

Matiz importante: hoy las cargas grandes de Qt no suelen viajar por
`runJavaScript`; viajan como mensajes embebidos en HTML estático. Por tanto, el
problema validado actual es doble:

1. El modelo estático impide una experiencia Qt fluida y conserva dos caminos de
   renderizado.
2. El canal vivo existente para comandos pequeños es inseguro porque no tiene
   readiness, cola, ack ni timeout.

La migración propuesta resuelve ambos problemas de forma conjunta.

## Objetivos

1. Cargar una shell HTML Qt una sola vez al iniciar la ventana.
2. Actualizar la escena mediante mensajes vivos Python -> JavaScript.
3. Unificar el contrato conceptual con AnyWidget/Jupyter.
4. Evitar pérdida silenciosa de mensajes.
5. Evitar saturación del canal Qt/Chromium con backpressure explícito.
6. Preservar el estado visual de la UI durante cargas y rebuilds cuando sea
   compatible con la operación.
7. Mantener la exportación HTML como salida reproducible independiente.
8. Mantener `_message_history` como fuente de verdad reproducible; los detalles
   de cola, acks, timeouts y estado Qt son runtime-only.

## No objetivos

- No introducir sincronización bloqueante en el hilo principal de Qt.
- No mandar animaciones continuas frame a frame desde Python si el frontend
  puede reproducirlas localmente.
- No hacer que acks, errores de transporte o estado efímero entren en
  `_message_history`.
- No sustituir inmediatamente el transporte Qt por `QWebChannel` si una capa
  ligera sobre `runJavaScript` y eventos JS -> Python cubre el caso 1.0.
- No usar el HTML exportado como estado interno de la aplicación Qt.

## Arquitectura propuesta

Separar tres capas:

1. Protocolo neutral.
2. Transporte concreto.
3. Política de cola/backpressure.

### Protocolo neutral

El protocolo debe ser independiente de Qt, Jupyter o export HTML. Los mensajes
Python -> JS siguen siendo `ViewerMessage`, ampliados de forma compatible con
metadatos opcionales:

```json
{
  "id": "qt-42",
  "generation": 7,
  "op": "load_molsys_payload",
  "payload": {}
}
```

Eventos JS -> Python:

```json
{
  "event": "ready"
}
```

```json
{
  "event": "message_ack",
  "id": "qt-42",
  "generation": 7,
  "op": "load_molsys_payload",
  "phase": "handled"
}
```

```json
{
  "event": "message_error",
  "id": "qt-42",
  "generation": 7,
  "op": "load_molsys_payload",
  "phase": "handled",
  "error": "..."
}
```

El frontend debe emitir `message_ack` después de que
`controller.handleMessage(msg)` termine correctamente. Si la operación falla,
debe emitir `message_error`.

Para operaciones que necesitan distinguir procesamiento lógico de primer render
visible, se definen fases adicionales:

```json
{
  "event": "structure_ready",
  "id": "qt-42",
  "generation": 7,
  "op": "load_molsys_payload"
}
```

```json
{
  "event": "render_ready",
  "id": "qt-42",
  "generation": 7,
  "op": "load_molsys_payload"
}
```

`message_ack` significa "mensaje procesado por el controlador".
`structure_ready` significa "las referencias internas de estructura necesarias
para capas, regiones, shapes y estilos ya existen". `render_ready` significa "la
escena asociada ya alcanzó un punto visual seguro para quitar spinners, capturar
imágenes, exportar figuras o reportar carga visible".

### Transporte

AnyWidget/Jupyter:

- Usa el transporte existente `model.send(...)` para eventos JS -> Python.
- Usa `widget.send(...)`/custom messages para Python -> JS.
- No debe depender de detalles Qt.

Qt/lite:

- Python -> JS: usar `page.runJavaScript(...)` con callback.
- JS -> Python: implementar un `notifyHost(event)` en `bootDocsView()`.
- Para Qt, `notifyHost(event)` debe usar inicialmente un esquema URL reservado,
  por ejemplo
  `molsysviewer://event?...`, interceptado por una subclase de
  `QWebEnginePage.acceptNavigationRequest(...)`.
- Para export HTML normal, `notifyHost(event)` debe ser no-op.

El esquema URL debe transportar sólo eventos pequeños. No debe usarse para
payloads moleculares, frames de película ni datos binarios grandes.

La primera implementación debe usar esquema URL, no `QWebChannel`. Si el esquema
URL resulta frágil, el contrato debe permitir sustituir el transporte Qt por
`QWebChannel` sin cambiar el protocolo de alto nivel.

### Política de cola Qt

Crear una pieza explícita en Python, por ejemplo `QtMessageBridge`, responsable
de:

- estado `ready`;
- cola de mensajes pendientes;
- generación actual de rebuild;
- IDs monotónicos de mensajes;
- despacho secuencial;
- callbacks de `runJavaScript`;
- recepción de `ready`, `message_ack`, `message_error`, `structure_ready` y
  `render_ready`;
- timeouts por clase de operación;
- coalescing de mensajes reemplazables;
- cancelación o ignorado de acks pertenecientes a generaciones antiguas;
- errores observables en status bar, logs o excepciones controladas según
  contexto.

El bridge es runtime-only. No debe modificar `_message_history`.

## Clases de mensajes

No todos los mensajes deben tener la misma política de cola.

### Lifecycle

Ejemplos:

- `clear_all`
- `load_molsys_payload`
- futuras operaciones de carga de payload por referencia

Política:

- orden estricto;
- ack obligatorio;
- timeout largo;
- generación obligatoria durante rebuilds;
- los acks de generaciones antiguas se ignoran.

### Scene/state

Ejemplos:

- capas;
- regiones;
- shapes;
- mediciones;
- estilos;
- replay de historia reproducible.

Política:

- orden relativo dentro de la generación;
- ack recomendado;
- timeout medio;
- no despachar antes de que el lifecycle principal haya terminado la fase
  requerida.

### UI

Ejemplos:

- `set_panel_mode`;
- acciones de navegación de panel;
- estado visual no reproducible.

Política:

- puede encolarse antes de `ready`;
- coalescing por clave si sólo importa el último estado;
- timeout corto;
- normalmente runtime-only.

### High frequency

Ejemplos:

- `set_trajectory_frame`;
- resize;
- cámara en vivo si se añade en el futuro;
- hover o preselección.

Política:

- coalescing obligatorio;
- no acumular cientos de mensajes obsoletos;
- evitar ack bloqueante por cada frame salvo en modo export/test;
- preferir playback local en JS para animaciones continuas.

## Generaciones de rebuild

Cada carga o rebuild vivo debe incrementar un `generation`.

Ejemplo:

1. El usuario carga demo A: generación 12.
2. Antes de terminar, carga demo B: generación 13.
3. Si llega tarde un ack de generación 12, Python lo ignora.
4. La cola activa continúa sólo con mensajes de generación 13.

Esto evita que respuestas tardías desbloqueen una escena obsoleta.

## Coalescing

La cola debe soportar claves de coalescing. Si hay mensajes pendientes con la
misma clave, el nuevo reemplaza al anterior.

Ejemplos:

- `set_panel_mode`: conservar sólo el último modo de panel.
- `set_trajectory_frame`: conservar sólo el último frame solicitado.
- resize: conservar sólo el último tamaño.
- cámara en vivo futura: conservar sólo la última cámara.

El coalescing no debe aplicarse a mensajes de carga, creación de capas, creación
de shapes, mediciones o cualquier operación donde cada mensaje represente una
mutación acumulativa.

## Migración del flujo Qt

### Antes

1. Python genera HTML con mensajes embebidos.
2. Qt recarga `QWebEngineView` con `setUrl(...)`.
3. El frontend lee mensajes iniciales y construye escena.
4. Comandos pequeños posteriores se envían con `runJavaScript` sin garantías.

### Después

1. Python genera o carga una shell HTML base.
2. Qt carga esa shell una vez.
3. El frontend inicializa MolSysViewer y emite `ready`.
4. Python marca el bridge como listo y despacha mensajes vivos.
5. Una carga de sistema ejecuta:
   - nueva generación;
   - `clear_all`;
   - `load_molsys_payload`;
   - espera de `structure_ready` antes de replay de escena;
   - replay de capas, regiones, shapes, mediciones y estado reproducible.
6. La UI permanece viva siempre que el rebuild no requiera reinicializar la
   shell completa.

## Relación con `_message_history`

La reproducibilidad no debe degradarse.

Reglas:

- `_message_history` sigue registrando sólo mensajes reproducibles.
- `_pending_messages` del widget no debe confundirse con la cola Qt runtime.
- IDs, generations, acks, timeouts, retries y estado del bridge son runtime-only.
- Export HTML debe reconstruirse desde la historia reproducible, no desde la
  cola Qt ni desde el estado vivo de `QWebEngineView`.
- Eventos de diagnóstico o errores del frontend pueden guardarse en estructuras
  runtime-only, no en historia exportable.

## Payloads grandes

Implementación actual:

- Usa `runJavaScript` para mensajes inline pequeños.
- Usa `json.dumps(...)` seguro y no construye scripts con interpolaciones
  frágiles más allá de insertar un literal JSON válido.
- Captura el callback de `runJavaScript` para saber si el frontend aceptó el
  mensaje.
- Convierte automáticamente `load_molsys_payload` a `load_molsys_payload_ref`
  cuando el tamaño serializado supera el umbral configurable
  `MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD`.
- Escribe el payload en un archivo temporal local y envía al frontend una
  referencia `file://`.
- Borra el archivo temporal al recibir `structure_ready`, `message_error`,
  timeout o cancelación de generación.

Contrato implementado:

- Operación `load_molsys_payload_ref`:

```json
{
  "id": "qt-99",
  "generation": 8,
  "op": "load_molsys_payload_ref",
  "ref": {
    "kind": "file",
    "url": "file:///tmp/molsysviewer-payload.json"
  }
}
```

- El frontend hace `fetch(ref.url)`, parsea el JSON y llama al mismo handler
  interno que `load_molsys_payload`.
- Esta vía reduce el tamaño de scripts inyectados y debe estar disponible para
  cargas Qt grandes.

Regla inicial:

- mantener `load_molsys_payload` inline para payloads pequeños y tests;
- usar `load_molsys_payload_ref` para cargas Qt grandes o cuando el tamaño
  serializado supere un umbral configurable;
- no borrar el archivo temporal hasta recibir ack/error de la carga asociada;
- validar con ventana Qt real que `fetch(file://...)` funciona en
  `QWebEngineView`; si no, usar un esquema local controlado o
  `QWebEngineUrlSchemeHandler`.

## Exportación HTML

El modelo vivo Qt no elimina la exportación HTML.

La exportación HTML debe seguir generando un documento autónomo desde la historia
reproducible. Ese HTML puede seguir usando mensajes iniciales embebidos porque es
una salida portable, no el mecanismo interno de la app Qt.

Implicación: el código debe distinguir claramente entre:

- shell Qt persistente;
- export HTML autónomo;
- docs/static views;
- AnyWidget/Jupyter.

## Exportación de películas y esperas Qt

Las esperas en rutas Qt no deben bloquear el procesamiento de eventos del hilo
principal.

Acción requerida:

- Introducir una utilidad Qt-local para esperas cooperativas que bombee eventos
  con `QCoreApplication.processEvents()` mientras espera acks o frames.
- No sustituir indiscriminadamente `time.sleep(...)` en código común si ese
  código también corre en Jupyter o backend no Qt.
- En modo export de película, los eventos `movie_frame` y `movie_export_done`
  deben poder volver a Python mientras la exportación espera.
- Las esperas deben tener timeout y reportar cuántos frames/eventos se recibieron
  antes de fallar.

## Frame changes y playback

El mensaje existente para cambio discreto de frame es:

```json
{
  "op": "set_trajectory_frame",
  "index": 24
}
```

No introducir `set_structure_index` salvo que se diseñe explícitamente como alias
o nuevo contrato.

Para playback continuo:

- preferir que JS/Mol* reproduzca localmente;
- Python debe enviar comandos de alto nivel (`play`, `stop`, frame puntual);
- evitar mandar 30/60 mensajes por segundo desde Python;
- si se sincroniza estado hacia Python, emitir eventos reducidos o por transición
  para no saturar el canal.

## Observabilidad y errores

El usuario no debe quedar ante una pantalla blanca indefinida.

Requisitos:

- Timeout diferenciado por tipo de mensaje.
- Error visible en status bar o diálogo Qt cuando una carga falla.
- Log de eventos de bridge en modo debug.
- Errores JS capturados y reenviados como `message_error` cuando estén asociados
  a un mensaje.
- Errores globales de frontend reportables como `frontend_error`.
- No ocultar silenciosamente fallos de readiness.

Timeouts orientativos iniciales:

- `ready`: 10 s.
- UI/control pequeño: 2-5 s.
- scene/state: 10-20 s.
- `load_molsys_payload`: 30 s o configurable.
- película/export: derivado del número de frames y resolución.

Estos valores son criterios iniciales; deben ajustarse con pruebas reales.

## Puntos de entrada del código actual

La implementación debe partir de estos puntos:

- `molsysviewer/standalone_qt/application.py`: creación de ventana,
  `QWebEngineView`, `QWebEnginePage` custom y carga inicial de la shell.
- `molsysviewer/standalone_qt/utils.py`: reemplazo de
  `_send_viewer_message()`, separación entre shell Qt persistente y export HTML,
  y helpers de carga viva.
- `molsysviewer/standalone_qt/menus.py`: acciones de carga y panel que hoy llaman
  a rebuild HTML, reload o envío fire-and-forget.
- `molsysviewer/standalone.py`: mantener `build_standalone0_html()` como ruta de
  exportación/documento autónomo; no convertirlo en el mecanismo Qt interno.
- `molsysviewer/viewer/core.py`: revisar `_rebuild_view_from_current_molsys()`,
  `_send()`, `_send_runtime_only()` y `_handle_frontend_event()` para integrar el
  backend Qt vivo sin contaminar historia reproducible.
- `molsysviewer/viewer/movie.py`: aislar esperas cooperativas Qt para export.
- `js/src/index.ts`: añadir `notifyHost`, ready/ack/error en `bootDocsView()`.
- `js/src/managers/viewer-controller.ts`: confirmar dónde termina
  `handleMessage()` para emitir ack fiable y dónde se puede emitir `render_ready`
  para cargas de estructura.
- `js/src/messages/viewer-messages.ts`: tipar metadatos opcionales `id` y
  `generation` sin romper los mensajes existentes.

## Detalles de transporte Qt

Si se usa esquema URL como primera implementación, deben cuidarse estos puntos:

- Crear una subclase de `QWebEnginePage` antes de cargar la shell y asignarla al
  `QWebEngineView`.
- Sobrescribir `acceptNavigationRequest(...)` para interceptar sólo el esquema
  reservado de MolSysViewer y devolver `False` después de procesarlo.
- No transportar JSON crudo sin codificar en la URL. Usar una codificación
  robusta, por ejemplo query parameter con `encodeURIComponent(JSON.stringify())`
  o base64url.
- Validar que el evento decodificado es un objeto con `event` string antes de
  pasarlo al dispatcher Python.
- Limitar tamaño de eventos JS -> Python; datos grandes deben viajar por otro
  mecanismo.
- Evitar que el esquema URL ensucie historial o navegación real del usuario. Si
  aparece ese problema, probar iframe oculto o migrar a `QWebChannel`.

La llamada Python -> JS debe devolver un valor observable. El script inyectado
debe evaluar a algo equivalente a:

```js
(() => {
  const handler = window.__molsysviewerDocsHandleMessage;
  if (typeof handler !== "function") return { accepted: false };
  Promise.resolve(handler(message)).catch((error) => {
    console.error("[MolSysViewer Qt bridge] message failed", error);
  });
  return { accepted: true };
})()
```

El callback Python de `runJavaScript` debe usar ese resultado para decidir si el
mensaje fue aceptado, si debe reintentarse o si debe fallar por timeout.

En layouts conda split, `qt6-webengine-uibcdf` instala recursos fuera de las
rutas que Qt WebEngine autodetecta en algunas ejecuciones. Antes de importar
`QtWebEngineCore`/`QtWebEngineWidgets`, `standalone_qt` debe configurar por
defecto, si existen y el usuario no las ha definido:

- `QTWEBENGINEPROCESS_PATH=$CONDA_PREFIX/libexec/QtWebEngineProcess`
- `QTWEBENGINE_RESOURCES_PATH=$CONDA_PREFIX/resources`
- `QTWEBENGINE_LOCALES_PATH=$CONDA_PREFIX/translations/qtwebengine_locales`

Esto no sustituye al empaquetado correcto. La validación con Qt real sigue
requiriendo que la build aporte todos los recursos que Chromium necesita,
incluido `icudtl.dat` cuando no esté embebido.

## Compatibilidad con rutas existentes

La migración no debe romper estas rutas:

- AnyWidget/Jupyter.
- Popup runtime.
- HTML autónomo exportado.
- Docs/static views.
- Exportación de figuras.
- Tests JS existentes sobre handlers.

Para ello, `notifyHost` debe degradar a no-op cuando no haya host, y los
metadatos `id`/`generation` deben ser opcionales para todos los handlers
existentes.

## Implementación sugerida por fases

### Fase 1: protocolo y host notification

- Añadir `notifyHost(event)` en `bootDocsView()`.
- Implementar no-op para HTML/export normal.
- Implementar transporte Qt por esquema URL interceptado.
- Emitir `ready` cuando el handler global y el controlador estén listos para
  procesar mensajes.
- Emitir `message_ack`/`message_error` desde el wrapper de
  `__molsysviewerDocsHandleMessage`.

### Fase 2: bridge Qt runtime-only

- Crear `QtMessageBridge` o equivalente en `standalone_qt`.
- Reemplazar `_send_viewer_message()` fire-and-forget por despacho con cola.
- Añadir IDs, generations, callbacks y timeouts.
- Añadir coalescing para mensajes UI/high-frequency.
- Añadir tests unitarios con fakes de `webview.page().runJavaScript(...)`.

### Fase 3: shell persistente Qt

- Cambiar `create_standalone_qt0_window()` para cargar una shell base.
- Reemplazar cargas de demo/fichero/PDB/source que hoy llaman a
  `_rebuild_qt_html()` + `setUrl(...)` por rebuild vivo:
  `clear_all` + `load_molsys_payload` o `load_molsys_payload_ref` + espera de
  `structure_ready` + replay.
- Mantener `load_molsys_payload_ref` para cargas Qt grandes y
  `load_molsys_payload` inline para payloads pequeños y tests.
- Mantener export HTML como acción explícita separada.

### Fase 4: rebuild vivo completo

- Integrar la lógica de `_rebuild_view_from_current_molsys()` con la cola Qt
  cuando el backend sea Qt vivo.
- Garantizar que capas, regiones, shapes, mediciones y estado reproducible se
  reenvían en orden correcto tras `load_molsys_payload`.
- Mantener estado visual de UI que no dependa de la estructura anterior.

### Fase 5: exportación y esperas cooperativas

- Encapsular esperas Qt con `QCoreApplication.processEvents()`.
- Asegurar que export de película puede recibir `movie_frame` y
  `movie_export_done` sin bloquear el canal.
- Añadir timeout y mensajes de error diagnósticos.

### Fase 6: medición y ajuste de payload refs

- Medir tamaños y estabilidad de `runJavaScript` inline.
- Ajustar umbral configurable de `load_molsys_payload_ref`.
- Si `fetch(file://...)` no es robusto en todos los entornos Qt soportados,
  migrar esa carga a un esquema local controlado o `QWebEngineUrlSchemeHandler`.

## Pruebas necesarias

### Unitarias Python

- Mensaje antes de `ready` queda en cola.
- `ready` vacía la cola en orden.
- `runJavaScript` con resultado negativo no descarta el mensaje.
- `message_ack` desbloquea el siguiente mensaje.
- `structure_ready` desbloquea replay de capas, regiones, shapes y estilos tras
  `load_molsys_payload`/`load_molsys_payload_ref`.
- `message_error` marca fallo observable.
- Timeout produce error controlado.
- Ack de generación antigua se ignora.
- Coalescing reemplaza mensajes pendientes de UI/high-frequency.
- Mensajes reproducibles siguen entrando en `_message_history`; metadatos del
  bridge no.

### Unitarias TypeScript

- `bootDocsView()` emite `ready`.
- El handler global emite `message_ack` al terminar `handleMessage`.
- El handler global emite `message_error` si `handleMessage` falla.
- La carga de payload emite `structure_ready` cuando las referencias internas de
  estructura ya existen.
- La carga de payload puede emitir `render_ready` para operaciones visuales,
  screenshots y export.
- `load_molsys_payload_ref` carga el mismo contrato que `load_molsys_payload`.
- `notifyHost` no rompe export HTML cuando no hay host.
- Mensajes con `id`/`generation` siguen siendo compatibles con los handlers
  existentes.

### Integración Qt manual o automatizada

- Abrir Qt y cargar demo sin recargar la shell.
- Cambiar repetidamente entre demos sin pantalla blanca.
- Abrir/cerrar paneles inmediatamente tras una carga sin pérdida de comandos.
- Cargar sistema mediano/grande y comprobar que hay timeout/error si falla.
- Verificar que export HTML sigue generando documento autónomo.
- Verificar que playback usa `set_trajectory_frame` para saltos puntuales y
  playback local para animación continua.

## Criterios de aceptación

1. `standalone_qt0` carga una shell HTML persistente y no usa regeneración de
   HTML como mecanismo interno para cargas normales.
2. Ningún mensaje Qt -> JS se pierde silenciosamente durante inicialización.
3. Las cargas vivas tienen IDs, generación y ack/error observable.
4. Los acks de generaciones obsoletas no alteran la cola activa.
5. Los mensajes reemplazables se coalescen y no saturan la cola.
6. La GUI Qt no se bloquea por esperas síncronas mientras necesita recibir
   eventos del frontend.
7. Export HTML conserva el comportamiento autónomo y reproducible.
8. La historia reproducible no incluye metadatos runtime-only del bridge.
9. Las pruebas unitarias cubren cola, ack, error, timeout, coalescing y
   generación.
10. La documentación de desarrollo explica la diferencia entre shell Qt viva,
    AnyWidget, export HTML y docs/static views.

## Riesgos y mitigaciones

Riesgo: el esquema URL para JS -> Python sea insuficiente o frágil.

Mitigación: mantener el protocolo independiente del transporte y poder migrar a
`QWebChannel` sin cambiar la semántica de mensajes.

Riesgo: `runJavaScript` con payloads grandes sea lento o tenga límites prácticos.

Mitigación: diseñar desde el principio la variante `payload_ref` y activarla si
las pruebas lo justifican.

Riesgo: el rebuild vivo deje residuos visuales en Mol*.

Mitigación: `clear_all` debe tener ack; las pruebas deben verificar cargas
sucesivas y que capas/shapes anteriores no sobreviven indebidamente.

Riesgo: preservar todo el estado UI pueda ser incorrecto cuando cambia la
estructura.

Mitigación: distinguir estado visual genérico preservable de estado dependiente
de la estructura. El segundo debe resetearse o validarse por generación.

Riesgo: la cola se convierta en una segunda fuente de verdad.

Mitigación: mantenerla runtime-only y reconstruible; la fuente reproducible sigue
siendo `_message_history`.

## Decisiones cerradas y abiertas

Decisiones cerradas:

- El transporte Qt inicial JS -> Python será esquema URL interceptado, no
  `QWebChannel`. El esquema **debe registrarse** (`registerScheme`) antes de la
  `QApplication`; hecho. `QWebChannel` queda como plan B si el esquema resulta
  lossy bajo carga, sin cambiar la semántica del bridge.
- El replay de capas, regiones, shapes y estilos esperará `structure_ready`, no
  necesariamente `render_ready`.
- Payloads grandes: **no** `fetch(file://...)` (bloqueado por Chromium). Se
  sirven por `QWebEngineUrlSchemeHandler` sobre `molsysviewer-payload://` en
  memoria. `load_molsys_payload` inline se mantiene para payloads pequeños/tests.

Decisiones abiertas:

- Confirmar en Qt real que el registro del esquema hace que el canal de eventos
  dispare de verdad y que el `fetch` del esquema de payload funciona (env-blocked).
- Decidir qué partes del estado UI se preservan entre cargas y cuáles se
  resetean por generación.
- Decidir si el bridge Qt vive sólo en `standalone_qt` o si se abstrae para otros
  hosts standalone futuros (deuda de duplicación con el modelo AnyWidget).
