# Propuesta de Mejora: Aislamiento del Espacio de Estado de Add-ons (State Namespace Isolation)

## 1. Contexto y Diagnóstico

En MolSysViewer, la sincronización de estado bidireccional entre los paneles interactivos de los add-ons y el backend de Python se realiza a través de un único diccionario centralizado en el widget (`addon_states` en `widget.py`).

Para garantizar el aislamiento entre diferentes add-ons, la clase base `AddonPanelWidget` expone la propiedad `state` y el método `set_state(updates)` en `molsysviewer/addons.py` (líneas 80-100). Sin embargo, el diagnóstico técnico revela una **vulnerabilidad crítica en cómo se resuelve el nombre del add-on para delimitar el espacio de nombres**:

```python
@property
def state(self) -> dict[str, Any]:
    if self._view is not None and hasattr(self._view.widget, "addon_states"):
        states = self._view.widget.addon_states or {}
        if self._view._active_panel_widget is not None:
            addon_name, _, _ = self._view._active_panel_widget
            return states.get(addon_name, {})
    return {}
```

El problema conceptual de aislamiento radica en que **la resolución del namespace del add-on depende del estado de visibilidad global del visor (`self._view._active_panel_widget`) en lugar de la identidad inmutable de la propia instancia del widget (`self`)**.

*Ejemplo de Falla*:
* Si un add-on ejecuta una tarea asíncrona o en segundo plano en Python (ej. una optimización matemática o cálculo de contactos a través de un hilo) e intenta actualizar su estado mediante `self.set_state(...)` cuando el usuario ya ha navegado a otra pestaña de add-on o ha cerrado el panel lateral:
  - `_active_panel_widget` será `None` o apuntará al nombre del *nuevo* add-on activo.
  - El add-on en segundo plano leerá o escribirá silenciosamente en el espacio de estado del add-on activo equivocado, o simplemente no guardará nada en el diccionario central.
  - Esto viola los principios fundamentales de encapsulamiento y aislamiento de estado.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Colisión de Datos e Inconsistencia**: Un add-on interactivo puede corromper silenciosamente los datos y variables de otro add-on si escribe en su namespace debido a que la interfaz de usuario cambió de pestaña activa durante una ejecución en segundo plano.
2. **Pérdida de Reactividad**: Las tareas científicas largas en Python no pueden actualizar su progreso o resultados de forma segura en la propiedad `state` del panel una vez que el usuario aparta la vista de ese panel, rompiendo la experiencia de usuario reactiva fluida.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Acoplamiento del Namespace a la Identidad Inmutable de la Instancia

Se propone rediseñar la resolución del espacio de nombres en `AddonPanelWidget` para que sea completamente independiente del estado de visibilidad del lienzo:

1. **Vincular el Nombre del Add-on en el Constructor**:
   Al instanciar el widget en `resolve_panel_widget(...)` (línea 1087), pasar explícitamente el nombre del add-on (`addon_name`) como un atributo privado e inmutable de la instancia (ej. `self._addon_name`):
   ```python
   # En ViewAddonsManager.resolve_panel_widget
   widget = cls(view=self._view)
   object.__setattr__(widget, "_addon_name", addon_name)
   return widget
   ```

2. **Resolver el Estado Usando el Atributo de la Instancia**:
   Modificar `state` y `set_state` en `AddonPanelWidget` para utilizar `self._addon_name` de forma incondicional, eliminando la dependencia de `self._view._active_panel_widget`:
   ```python
   @property
   def state(self) -> dict[str, Any]:
       addon_name = getattr(self, "_addon_name", None)
       if self._view is not None and addon_name is not None and hasattr(self._view.widget, "addon_states"):
           states = self._view.widget.addon_states or {}
           return states.get(addon_name, {})
       return {}

   def set_state(self, updates: dict[str, Any]) -> None:
       addon_name = getattr(self, "_addon_name", None)
       if self._view is not None and addon_name is not None and hasattr(self._view.widget, "addon_states"):
           states = dict(self._view.widget.addon_states or {})
           addon_state = dict(states.get(addon_name, {}))
           addon_state.update(updates)
           states[addon_name] = addon_state
           self._view.widget.addon_states = states
   ```

---

## 4. Criterios de Aceptación

1. Las lecturas y escrituras de estado mediante `self.state` y `self.set_state()` en un `AddonPanelWidget` deben operar estrictamente sobre el namespace único del add-on al que pertenece el widget, independientemente de cuál sea el add-on activo en la interfaz de usuario en ese instante.
2. Las tareas asíncronas en Python deben poder actualizar el estado de su panel correspondiente de forma segura y aislada en segundo plano.
3. Se deben añadir pruebas unitarias que simulen múltiples widgets de add-ons activos en memoria y validen que sus escrituras de estado no colisionan ni se alteran bajo cambios simulados del panel activo del visor.
