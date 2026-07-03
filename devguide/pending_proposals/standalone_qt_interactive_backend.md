# Propuesta: backend Qt interactivo (MolSysView persistente sobre el bridge)

## Estado

Pendiente. Continuación de `standalone_qt_live_model` (ya **cerrado**: el modelo
vivo de mensajes de **carga** está implementado y validado en Qt real —
shell persistente, `QtMessageBridge` con ids/generación/ack/error/coalescing,
esquemas `molsysviewer://` (eventos) y `molsysviewer-payload://` (datos), y una
carga reproduce la escena entera). La arquitectura de superficies está en
`docs/content/developer/standalone_surfaces.md`.

## Problema

El host Qt **no tiene un `MolSysView` persistente** ligado al bridge. Hoy
`_build_qt_live_messages` crea un `MolSysView` **temporal**, lo serializa con
`_build_export_messages()` y lo descarta; manda dicts crudos al webview. Por eso:

- Las **cargas** funcionan (snapshot reproducible → mensajes vivos).
- Pero **no hay `_handle_frontend_event` que reciba eventos**, así que en Qt no
  funcionan: interacciones (hover/click/context-menu, `on_frame_change`),
  export de película, ni ediciones dinámicas (añadir shapes/regiones en vivo,
  rebuilds tras cambiar la topología). El `bridge.handle_frontend_event` solo
  procesa los eventos del propio bridge (ready/ack/error/…) e ignora el resto.

Para que Qt sea una superficie de producto **interactiva** (no solo un cargador),
hay que promover el host Qt al mismo modelo que AnyWidget: **el `MolSysView` es el
backend, el bridge es el transporte**.

## Progreso

**F1 implementado** (pendiente validación en Qt real): `QtViewChannel` (canal
que satisface la interfaz `widget` del view), `event_sink` en el bridge que
reenvía los eventos de producto al view, `MolSysView(transport=…)`, y el host Qt
crea **un** `MolSysView` persistente que conduce las cargas con `view.load(...,
mode="replace")` (en vez del snapshot temporal), con `view._qt_process_events =
app.processEvents`. Verificado con fakes + molsysmt real; falta el round-trip en
ventana Qt real. **Esto habilita F2 y F3** (ya reciben eventos), que quedan
principalmente como *validación* + glue de UI.

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

1. En Qt, un `view.load(...)` y un rebuild pasan por el bridge con generación y ack.
2. Los eventos del frontend (interacción, movie, acks de escena) llegan al
   `MolSysView` persistente.
3. Export de película funciona en Qt sin bloqueo, con timeout.
4. Hover/click y una edición dinámica (p. ej. `add_sphere`) funcionan sin recargar.
5. `_message_history` sigue siendo la única fuente reproducible; export HTML intacto.
6. Tests de enrutado de eventos, movie y edición dinámica en verde.

## Riesgos

- **Duplicación con AnyWidget:** este es el momento de extraer de verdad el
  "transporte neutral" (hoy aspiracional) para no mantener dos backends vivos
  divergentes. La abstracción de canal de F1 debería servir a ambos.
- **Bloqueo del hilo:** cualquier espera nueva debe usar la primitiva cooperativa,
  nunca `time.sleep` a secas en contexto Qt.
- **Orden de replay:** el rebuild vivo debe respetar `structure_ready` antes de
  reenviar capas/regiones/shapes (ya decidido en el documento anterior).
