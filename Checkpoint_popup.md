# MolSysViewer — Popout Vivo/Espejo (Checkpoint)

## Objetivo
- Botón “Pop” que abra una ventana independiente con el mismo visor, interactiva (rotación, controles, cámara) y sincronizada en vivo con el host.
- Toggle: al pulsar de nuevo, cerrar el popout; si el popout se cierra, el estado se resetea.
- Sincronía: todas las acciones Python→JS (load, regiones, layers/shapes, hide/show, presets, etc.) se reflejan en el popout. Opcionalmente, acciones de cámara/controles en el popout podrían reflejarse en el host (fase siguiente).

## Estado actual
- Se añadió botón “Pop” en la UI.
- Al pulsar, se abre una ventana nueva con contenedor, controlador MolSysViewer y controles básicos (Reset/Full/Bg/Spin/Swing).
- `window.MolSysViewerController` se expone para reutilizar la clase en el popout.
- Se mantiene `messageLog` con todas las acciones (incluido load inicial) y se reenvía al popout al abrirlo; cada mensaje Python→JS nuevo se duplica en vivo hacia el popout.
- Popout se cierra si se vuelve a pulsar Pop; si se cierra manualmente, se resetea el estado.
- Unidireccional: host → popout. El popout no envía eventos de vuelta (cámara/controles) al host.

## Problemas/limitaciones
- Hay que verificar que el popout es plenamente interactivo (rotación/ratón); en versiones previas se veía vacío/sólo ejes.
- No es espejo bidireccional: lo que se hace en el popout no actualiza el host.
- No hay cierre/cleanup en `clear_all/reset`; podría quedar popout zombie si se limpia el viewer.
- Seguridad: `postMessage` usa `"*"`; ajustar si se requiere restringir a mismo origen.

## Próximos pasos (ruta)
1) Verificar interactividad en popout: que la escena se carga y la cámara responde.
2) Replicar overlay completo en el popout (incluyendo controles de trayectoria si aplica) y estilos.
3) Limpieza ciclo de vida: cerrar o re-sincronizar el popout en `clear_all/reset`; actualizar estado del botón al detectar cierre.
4) Canal opcional popout→host (fase 2): permitir cámara/controles desde el popout, evitando bucles de eco.
5) Robustez de mensajes: asegurar que `messageLog` contiene todo (initial_messages + acciones posteriores) y manejo de errores en popout.
6) Ajustar origen en `postMessage` si se endurece la política.

## Cómo probar ahora
- En notebook: pulsar Pop; la ventana debe mostrar la estructura cargada y responder a controles básicos. Ejecutar acciones (new_region, add_shape, hide/show) en el host y comprobar que se replican en el popout.
- Rotación/cámara en popout: verificar si responde (por ahora solo host→popout).

## Falta por hacer
- Confirmar interactividad completa y recepción de todos los mensajes en popout.
- Añadir cleanup en reset/clear_all.
- (Opcional) Sincronía bidireccional de cámara/controles.
- Documentar uso y limitaciones (unidireccional por ahora).
