# MolSysViewer — Popout Vivo/Espejo (Checkpoint)

## Objetivo
- Botón “Pop” que abra una ventana independiente con el mismo visor, interactiva (rotación, controles, cámara) y sincronizada en vivo con el host.
- Toggle: al pulsar de nuevo, cerrar el popout; si el popout se cierra, el estado se resetea.
- Sincronía: todas las acciones Python→JS (load, regiones, layers/shapes, hide/show, presets, etc.) se reflejan en el popout. Opcionalmente, acciones de cámara/controles en el popout podrían reflejarse en el host (fase siguiente).

## Estado actual (2025-12-07)
- Se añadió botón “Pop” en la UI del host (overlay).
- Al pulsar, se abre una ventana nueva con contenedor, controlador MolSysViewer y controles completos (Reset/Full/Bg/Spin/Swing + controles de trayectoria).
- El popup puede cargar el bundle JS de dos formas:
  - **Blob URL** si se proporciona el código fuente (`popup_js_source` o `_esm`).
  - **URL de módulo** si se pasa una ruta `moduleUrl` (exports docs-light con
    runtime compartido, p.ej. `molsysviewer-runtime.js`).
- Se mantiene un `commandLog`/`commandLog` (historial de mensajes) y se reenvía al popup en `molsysviewer-initial-sync`; cada mensaje Python→JS nuevo se duplica en vivo hacia el popout como `molsysviewer-sync-op`.
- El popup notifica cuando está listo (`molsysviewer-pop-ready`) y queda marcado como `isReady` en el host.
- Popout se cierra si se vuelve a pulsar Pop; si se cierra manualmente, el host detecta el cierre y resetea `isReady`/referencias.
- Sincronización de cámara bidireccional condicionada por interacción:
  - Host → popup: se suscribe a `canvas3d.didDraw` y envía `molsysviewer-sync-camera` sólo cuando el usuario interactúa en el host.
  - Popup → host: el popup también se engancha a `didDraw` y envía snapshots sólo cuando el usuario interactúa en el popup.
- Autohide de controles sincronizado: cambios en `autohide_controls` se envían al popup y éste ajusta listeners de `pointerenter/leave`.
- El popup replica los controles principales (incluida trayectoria) y los opera sobre su propio controller, re-enviando las operaciones (`molsysviewer-sync-op`) al host.
- El botón Pop puede desactivarse desde el host con `enable_popout=False` (trait sincronizado).

## Problemas/limitaciones actuales
- Seguridad: `postMessage` sigue usando `"*"`; si en el futuro se endurece CSP u orígenes cruzados, habrá que restringirlo a mismo origen.
- El popup asume que el bundle JS se puede importar desde un Blob URL; si en algún entorno esto falla (navegadores muy antiguos), habría que introducir un fallback.
- El ciclo de vida está sincronizado a nivel de ventana, pero no se fuerza el cierre del popup en todos los resets del viewer (se deja al usuario cerrar o reabrir).

## Próximos pasos (ruta)
1) Afinar UX de sync de cámara (umbrales/tiempos para marcar “interacción de usuario” en host/popup).
2) Añadir, si es necesario, una opción explícita para cerrar el popup desde Python (API) además del botón en la UI.
3) Documentar claramente en la guía de usuario el comportamiento del popout y las limitaciones de seguridad (`postMessage("*")`).
4) Evaluar si es necesario restringir el origen de `postMessage` cuando el visor se use en entornos más estrictos (servidores multi-tenant, etc.).

## Cómo probar ahora
- En notebook: pulsar Pop; la ventana debe mostrar la estructura cargada y responder a controles y rotación/cámara igual que el host.
- Ejecutar acciones en el host (load, `new_region`, `new_layer`, `shapes.add_*`, `hide/show`, presets globales) y comprobar que se replican en el popout.
- Probar controles en el popup (reset, background, spin/swing, trayectoria) y verificar que sus efectos se reflejan en el host sin “pelea” de cámara.

## Falta por hacer
- Revisar seguridad de `postMessage` y orígenes en despliegues no locales.
- Añadir tests E2E específicos para escenarios con popout si se considera necesario (actualmente se prueba sobre todo el flujo de regiones/visibilidad).
