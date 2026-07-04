# Standalone Qt — known issues (backend interactivo)

Extraídos al cerrar `standalone_qt_interactive_backend` (validado en Qt real /
GPU el 2026-07-04). El núcleo del backend interactivo funciona en producto
(render, transporte, `MolSysView` persistente, context menu, interacción de
cámara). Estos 2 quedan pendientes, **deprioritized**.

## 1. Load Demo no reemplaza el sistema en vivo

**Síntoma:** en la ventana Qt real, `File → Load Demo → <otro sistema>` no cambia
la escena; sigue viéndose el sistema anterior (ni siquiera se limpia).

**Diagnóstico (hecho):** el lado Python **emite correctamente**. Con `MolSysView`
real + `QtViewChannel` + bridge fake, el flujo de Load Demo
(`bridge.begin_generation()` + `view.load(target, mode="replace")`) envía, con
`view._ready == True`, exactamente:

```
op: clear_all
op: load_molsys_payload
```

Es decir, el fallo **no está en el emit de Python** sino en el **frontend /
transporte** de la 2ª generación: el `clear_all` y/o el payload de la nueva
generación no se aplican en el frontend en Qt real.

**Pistas para investigar:**
- ¿El frontend recibe y ejecuta el `clear_all` + `load_molsys_payload` de la 2ª
  carga? (instrumentar `handleMessage` en `js/src/index.ts`).
- El payload va por `molsysviewer-payload://` (ref scheme handler). ¿Se **sirve**
  el payload de la 2ª carga, o el handler tiene estado obsoleto / colisión de id
  entre generaciones? Revisar `_make_payload_scheme_handler` y `served`.
- ¿Interfiere `begin_generation` (limpia cola / `inflight=None`) con el flush de
  los mensajes recién encolados? Verificar orden y `bridge.ready`.

## 2. Export Movie: "no camera snapshot available"

**Síntoma:** `Export → Export Movie (orbit)` falla con *"no camera snapshot
available"*.

**Diagnóstico:** `movie.add_camera_orbit()` parte del estado de cámara actual, y
en el contexto Qt `view._last_camera_snapshot` está a `None` — falta el
round-trip de petición de cámara (pedir snapshot → el frontend responde →
`_last_camera_snapshot`).

**Pistas para investigar:**
- El frontend emite `camera_snapshot`; ¿se enruta ese evento al view persistente
  vía el bridge (`event_sink` → `_handle_frontend_event`)?
- ¿La acción de export debería **pedir** un snapshot y **esperarlo** (espera
  cooperativa con `view._qt_process_events`) antes de `add_camera_orbit`?
- Alternativa: `add_camera_orbit` que tolere ausencia de snapshot usando una
  cámara por defecto.
