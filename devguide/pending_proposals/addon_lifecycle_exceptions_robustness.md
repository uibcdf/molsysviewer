# Propuesta de Mejora: Robustez y Control de Excepciones en el Ciclo de Vida de Add-ons

## 1. Contexto y Diagnóstico

MolSysViewer proporciona una infraestructura de ciclo de vida para add-ons a través de `AddonLifecycleSpec` y el gestor `ViewAddonsManager` en `molsysviewer/addons.py`. El gestor invoca callbacks en Python ante eventos clave de la sesión, tales como `lifecycle.on_enable(view)` al activar el add-on, `lifecycle.on_disable(view)` al desactivarlo, y `handler(view, action_id, payload)` al responder a acciones contextuales.

El problema de robustez radica en que **estas llamadas críticas no están protegidas contra excepciones en el código de los add-ons**. Si el código de un add-on (por ejemplo, desarrollado por la comunidad o en fase de pruebas) lanza un error o excepción de Python durante la activación o al procesar una acción:
* La excepción se propaga directamente, interrumpiendo el flujo de ejecución del kernel de Python del usuario.
* El gestor de add-ons queda a medio sincronizar (ej. un add-on marcado como activo pero cuyos callbacks de inicialización fallaron o dejaron variables corruptas).
* Existe una inconsistencia con otros hooks como `on_active_selection_changed` (línea 1063), el cual sí cuenta con una envoltura `try-except` protectora que silencia el error para evitar colapsos.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Interrupción Crítica de la Sesión**: Un fallo en un add-on secundario o una acción contextual errónea puede abortar la ejecución completa de la celda de Jupyter del usuario, interrumpiendo su flujo de trabajo e investigación molecular.
* **Inestabilidad del Visor**: El visor puede quedar en un estado inconsistente (incoherencia de liveness de add-ons), obligando al investigador a reiniciar el kernel y recargar el visor completo para restablecer la sesión.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Envoltura Protectora Homogénea de Callbacks de Ciclo de Vida

Se propone robustecer la invocación de callbacks en `ViewAddonsManager` aplicando un patrón homogéneo de aislamiento de excepciones:

1. **Aislar Activación y Desactivación (`on_enable` / `on_disable`)**:
   En los métodos `_activate_addon` (línea 930) y `_deactivate_addon` (línea 938) de `ViewAddonsManager`, envolver los callbacks en bloques `try-except`:
   ```python
   def _activate_addon(self, name: str) -> None:
       if name in self._active_runtime:
           return
       lifecycle = self._host.lifecycle_for(name, skip_digestion=True)
       if lifecycle is not None and lifecycle.on_enable is not None:
           try:
               lifecycle.on_enable(self._view)
           except Exception as e:
               # Registrar el error sin abortar la sincronización del visor
               logger.error(f"Failed to enable add-on {name!r}: {e}", exc_info=True)
               # Opcional: enviar un mensaje de error al frontend
               self._view._send_runtime_only({
                   "op": "backend_error_occurred",
                   "error_message": f"Addon {name!r} failed to enable: {e}"
               })
               return  # Evitar marcarlo como activo si falló la inicialización
       self._active_runtime.add(name)
   ```

2. **Aislar Acciones Contextuales (`handle_context_action`)**:
   En el método `handle_context_action` (línea 1032), envolver la invocación del handler en un bloque protector equivalente:
   ```python
   try:
       handler(self._view, action_id, dict(payload))
   except Exception as e:
       logger.error(f"Error in context action {action_id!r} of add-on {addon!r}: {e}", exc_info=True)
       self._view._send_runtime_only({
           "op": "backend_error_occurred",
           "error_message": f"Context action {action_id!r} failed: {e}"
       })
       return False
   ```

---

## 4. Criterios de Aceptación

1. Los fallos o excepciones lanzados en los callbacks de ciclo de vida (`on_enable`, `on_disable`, `on_context_action`) de un add-on no deben colapsar el kernel de Python ni interrumpir la ejecución de celdas del usuario.
2. Si un callback de activación (`on_enable`) de un add-on falla, el gestor debe atrapar el error, registrarlo, notificar visualmente al usuario en la UI y evitar marcar el add-on como activo para mantener la coherencia.
3. Se deben incorporar pruebas unitarias que simulen add-ons defectuosos (cuyos callbacks lancen excepciones deliberadas) y convaliden que el visor permanece estable y operativo.
