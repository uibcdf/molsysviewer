# Propuesta: backend Qt interactivo (MolSysView persistente sobre el bridge)

## Estado

**Validado en Qt real (aleph, GPU + pantalla, 2026-07-04).** El único gate que
quedaba —render WebGL funcional en una ventana Qt real— está superado. El núcleo
del backend interactivo funciona en producto:

- ✅ Render 3D en GPU (dialanine visible; zoom/rotación con ratón).
- ✅ Transporte JS→Python (`fetch("molsysviewer://event")` → handler → bridge).
- ✅ Context menu nativo (F3): click derecho despliega el menú y "Reset view" funciona.
- ✅ `MolSysView` persistente ligado al bridge, con eventos de producto enrutados
  al view.

(El instalable de la familia Qt-for-Python está publicado en el canal `uibcdf`, así
que esto se prueba sin compilar — ver `project_standalone_packaging`.)

### Known issues (deprioritized — no bloquean el núcleo)

- **Load Demo no reemplaza el sistema en vivo** (F1): el Python **sí emite**
  `clear_all` + `load_molsys_payload` con `view._ready=True` (comprobado con
  `MolSysView` real + `QtViewChannel` + bridge fake), así que el fallo es
  frontend/transporte — el `clear_all` o el payload de la 2ª generación no se
  aplican en el frontend.
- **Export Movie: "no camera snapshot available"** (F2): `add_camera_orbit`
  necesita un snapshot de cámara no disponible en el contexto Qt (falta el
  round-trip de petición de cámara / `_last_camera_snapshot` a None).

Estos 2 quedan como follow-up acotado; el resto de la propuesta (abajo) es el
registro de diseño e implementación.

Continuación de `standalone_qt_live_model` (ya **cerrado**: el modelo vivo de
mensajes de **carga** está implementado — shell persistente, `QtMessageBridge`
con ids/generación/ack/error/coalescing, esquemas `molsysviewer://` para eventos
y `molsysviewer-payload://` para datos). La arquitectura de superficies está en
`docs/content/developer/standalone_surfaces.md`.

## Problema

El problema original era que el host Qt **no tenía un `MolSysView` persistente**
ligado al bridge. Antes, `_build_qt_live_messages` creaba un `MolSysView`
**temporal**, lo serializaba con `_build_export_messages()` y lo descartaba;
mandaba dicts crudos al webview. Por eso:

- Las **cargas** funcionan (snapshot reproducible → mensajes vivos).
- Pero **no hay `_handle_frontend_event` que reciba eventos**, así que en Qt no
  funcionan: interacciones (hover/click/context-menu, `on_frame_change`),
  export de película, ni ediciones dinámicas (añadir shapes/regiones en vivo,
  rebuilds tras cambiar la topología). El `bridge.handle_frontend_event` solo
  procesa los eventos del propio bridge (ready/ack/error/…) e ignora el resto.

La solución implementada promueve el host Qt al mismo modelo conceptual que
AnyWidget: **el `MolSysView` es el backend, el bridge es el transporte**.

## Progreso

**F1 implementado** (pendiente validación visual en Qt real): `QtViewChannel` (canal
que satisface la interfaz `widget` del view), `event_sink` en el bridge que
reenvía los eventos de producto al view, `MolSysView(transport=…)`, y el host Qt
crea **un** `MolSysView` persistente que conduce las cargas con `view.load(...,
mode="replace")` (en vez del snapshot temporal), con `view._qt_process_events =
app.processEvents`. Verificado con fakes + `molsysmt` real.

**F2 y F3 implementados** (glue de UI incluido, pendiente validación visual en Qt
real):
- Enrutado de eventos probado end-to-end (un `interaction_click` reenviado
  actualiza el estado del view; un `movie_frame` cae en el buffer de export).
- **F3**: acción de menú contextual nativa (`QMenu` en click derecho vía
  `view.on_context`, "Reset view").
- **F2**: acción de menú "Export Movie (orbit)" que hace `add_camera_orbit` +
  `movie.export` sobre el view persistente (la espera cooperativa bombea el bucle
  Qt con `view._qt_process_events`).
- **Transporte JS -> Python validado con Qt real mínimo**: la vía original por
  navegación (`iframe`, `window.location`, `anchor`) a `molsysviewer://event`
  no dispara `acceptNavigationRequest` en Qt real (`about:blank#blocked` o
  silencio). Se reemplazó por `fetch("molsysviewer://event?...")` servido por
  `QWebEngineUrlSchemeHandler`; el smoke mínimo sin Mol*/WebGL confirma que
  `ready` llega a Python y pone `bridge.ready=True`.

Lo único pendiente de F1/F2/F3 es **verlo correr en una ventana Qt real con render
funcional**: carga visible, context menu mostrándose, y una película exportada
sin bloqueo.

## Validacion realizada

- Tests unitarios/fakes para el bridge, el `QtViewChannel`, el view persistente,
  eventos de interaccion, eventos de pelicula, handler de payloads y handler de
  eventos.
- Tests con `molsysmt` real dentro de la suite Python.
- Smoke Qt mínimo con HTML sin Mol*/WebGL: `fetch("molsysviewer://event?...")`
  llega al handler Python y pone `bridge.ready=True`.
- Suite Python completa en verde.
- Tests JS en verde tras reconstruir el runtime.

## Validacion pendiente

- Cargar una molecula en una ventana Qt real y confirmar `structure_ready` +
  render visible.
- Confirmar que el context menu nativo aparece en click derecho y ejecuta la
  accion esperada.
- Exportar una pelicula corta y confirmar que no bloquea el hilo principal.
- Verificar una edicion dinamica post-carga, por ejemplo `add_sphere(...)`, sin
  recargar la shell.

## F1 — `MolSysView` persistente ligado al bridge (núcleo) — HECHO

- Crear **un** `MolSysView` en `create_standalone_qt0_window`, con vida = la de la
  ventana.
- **Salida (Python → JS):** enrutar `view._send` / `_send_runtime_only` a través
  del bridge (`webview` → `QtMessageBridge.send`) en vez del enfoque
  snapshot-y-descartar. En la práctica: darle al `MolSysView` un "canal" Qt igual
  que hoy tiene el `widget` de AnyWidget (una abstracción de transporte que
  `_send`/`_send_runtime_only` usan). Reemplazar `_build_qt_live_messages` por
  `view.load(...)` real, que emite `clear_all` + escena por el bridge con
  `new_generation`.
- **Entrada (JS → Python):** que `bridge.handle_frontend_event` **reenvíe los
  eventos no-bridge** (`interaction_*`, `movie_*`, `region_ack`, `layer_ack`,
  `trajectory_frame_changed`, `panel_mode_state`, …) a `view._handle_frontend_event`.
- Fijar `view._qt_process_events = app.processEvents` (consumidor de la primitiva
  de espera cooperativa que ya existe).
- **Reproducibilidad:** `_message_history` sigue siendo la fuente de verdad; el
  export HTML se reconstruye desde ahí, no desde el estado vivo del webview.
- **Rebuild vivo:** integrar `_rebuild_view_from_current_molsys()` con la cola Qt
  (Fase 4 del documento original): `clear_all` con ack + replay ordenado.
- **Tests:** enrutado de un evento de interacción de ida y vuelta con fakes; que
  `view._send` en contexto Qt encola en el bridge y no en `widget._pending`.

**Esfuerzo:** alto. Es el desbloqueo del que dependen F2 y F3.

## F2 — Export de película en Qt (depende de F1)

- Con F1, `movie_frame` / `movie_export_done` llegan a `view._handle_frontend_event`
  (rellenan `_movie_export_frames` / `_movie_export_done`).
- La **primitiva de espera cooperativa ya existe** en `movie.py` (bombea
  `view._qt_process_events`); solo faltaba consumidor.
- **Test/validación:** exportar una película corta en Qt sin bloquear el hilo
  principal, con timeout y reporte de frames recibidos.

**Esfuerzo:** bajo-medio.

## F3 — Interacciones y ediciones dinámicas (depende de F1)

- Hover/click/context-menu, `on_hover`/`on_click`/`on_frame_change`, y añadir
  shapes/regiones/mediciones en vivo caen automáticamente una vez el view
  persistente recibe eventos y emite por el bridge.
- **UI:** conectar el context-menu Qt (nativo o web) a `interaction_context_menu`.
- **Tests:** round-trip de hover/click; que un `add_sphere(...)` tras la carga
  emite por el bridge y aparece sin recargar.

**Esfuerzo:** medio.

## Criterios de cierre

Cumplidos a nivel de código/fakes:

1. `view.load(...)` y los mensajes del view persistente pasan por el bridge con
   generación y ack.
2. Los eventos del frontend (interacción, movie, acks de escena) llegan al
   `MolSysView` persistente cuando el bridge los recibe.
3. `_message_history` sigue siendo la única fuente reproducible; export HTML
   intacto.
4. Tests de enrutado de eventos, movie y edición dinámica en verde.

Pendientes de validación real:

1. En Qt real, carga visible con `structure_ready` y render WebGL.
2. Export de película funciona en Qt sin bloqueo, con timeout.
3. Hover/click/context-menu y una edición dinámica funcionan sin recargar.

## Riesgos

- **Duplicación con AnyWidget:** este es el momento de extraer de verdad el
  "transporte neutral" (hoy aspiracional) para no mantener dos backends vivos
  divergentes. La abstracción de canal de F1 debería servir a ambos.
- **Bloqueo del hilo:** cualquier espera nueva debe usar la primitiva cooperativa,
  nunca `time.sleep` a secas en contexto Qt.
- **Orden de replay:** el rebuild vivo debe respetar `structure_ready` antes de
  reenviar capas/regiones/shapes (ya decidido en el documento anterior).
