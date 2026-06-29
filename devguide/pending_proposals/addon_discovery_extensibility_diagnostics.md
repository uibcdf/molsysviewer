# Propuesta Pendiente: Mostrar Fallos de Descubrimiento de Add-ons en la UI

## Estado Actual

La parte de backend del descubrimiento dinámico ya está implementada:

- `GlobalAddonsRegistry.discover()` descubre add-ons mediante entry points estándar de Python en el grupo `molsysviewer.addons`.
- `KNOWN_ADDON_MODULES` se conserva sólo como fallback de compatibilidad para los add-ons históricos.
- Los fallos durante discovery se registran en `addons.discovery_failures()` con `source`, `reason` y `traceback` completo.
- Hay pruebas unitarias para discovery mediante entry points simulados y para fallos de carga diagnosticables.

## Pendiente Real

Falta exponer esos diagnósticos de forma visible en la interfaz interactiva del visor.

Actualmente el usuario o desarrollador puede consultar los fallos desde Python con:

```python
from molsysviewer import addons
addons.discovery_failures()
```

pero no hay todavía un aviso no obstructivo en Jupyter/Workbench que indique que un add-on instalado no se cargó.

## Propuesta Pendiente

Añadir una superficie de UI para los fallos reportados por `addons.discovery_failures()`:

1. Enviar al frontend un resumen de fallos de discovery durante la inicialización del visor o al refrescar add-ons.
2. Mostrar un aviso discreto en el panel/workbench, por ejemplo:
   `1 add-on failed to load. Open diagnostics for traceback.`
3. Permitir consultar el `traceback` completo desde esa UI sin interrumpir la carga normal del visor.

## Criterios de Aceptación Restantes

1. Si un entry point de add-on falla al cargar, el visor debe mostrar una señal visible de diagnóstico en la UI interactiva.
2. El usuario debe poder inspeccionar `source`, `reason` y `traceback` desde la UI.
3. La UI debe ser no obstructiva: el visor y los demás add-ons deben seguir funcionando.
