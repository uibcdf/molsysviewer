# Propuesta de Mejora: Descubrimiento Dinámico y Diagnóstico de Carga de Add-ons

## 1. Contexto y Diagnóstico

MolSysViewer implementa el descubrimiento automático de extensiones en `GlobalAddonsRegistry.discover(...)` en `molsysviewer/addons.py`. Por defecto, el visor escanea el entorno de Python intentando importar los módulos descritos en la tupla estática y cableada `KNOWN_ADDON_MODULES` (líneas 378-382):

```python
KNOWN_ADDON_MODULES: tuple[str, ...] = (
    "molsysviewer_topomt",
    "molsysviewer_pharmacophoremt",
    "molsysviewer_elasnetmt",
)
```

Este esquema presenta dos limitaciones conceptuales severas de extensibilidad y diagnóstico:
1. **Acoplamiento Rígido (Hardcoding)**: Para que un nuevo add-on desarrollado por la comunidad científica sea "descubierto" automáticamente por el visor, su nombre debe ser previamente inyectado en el código central de MolSysViewer. Esto rompe los principios de extensibilidad orgánica desacoplada.
2. **Silencio Diagnóstico en Fallas de Importación**: Si un módulo de add-on está instalado en el entorno pero su importación falla debido a un error interno (ej. un bug de sintaxis, una dependencia de tercer nivel rota o una versión de numpy incompatible), el método `discover` atrapa la excepción de forma silenciosa para evitar colapsar la inicialización general. Emite una alerta a SMonitor (`addon_load_failed`), pero **no proporciona ninguna retroalimentación visual o diagnóstica clara en el entorno interactivo de Jupyter**, dejando al desarrollador sin saber por qué su extensión simplemente no se muestra en la interfaz del visor.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Barreras para la Comunidad**: Los desarrolladores de la comunidad científica no pueden distribuir sus add-ons de forma independiente con autodescubrimiento nativo; sus usuarios deben habilitarlos manualmente mediante código explícito (`view.addons.manager.register_module(...)`).
* **Frustración en el Desarrollo**: Cuando un desarrollador edita su extensión e introduce un error de importación, el add-on desaparece misteriosamente del lienzo lateral de Jupyter en la siguiente recarga del visor. Al no recibir ningún reporte o traza de error en la celda, el desarrollador pasa horas intentando diagnosticar un fallo silencioso de carga.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

Se propone transformar el descubrimiento de add-ons en un sistema dinámico, desacoplado y transparente:

1. **Adoptar Puntos de Entrada Estándar de Python (`entry_points`)**:
   En lugar de escanear la tupla estática `KNOWN_ADDON_MODULES`, utilizar el sistema de metadatos de paquetes de Python (`importlib.metadata`) para descubrir extensiones registradas dinámicamente bajo un grupo de puntos de entrada común, por ejemplo `molsysviewer.addons`:
   ```python
   # En GlobalAddonsRegistry.discover
   from importlib.metadata import entry_points
   
   discovered_entries = entry_points(group="molsysviewer.addons")
   for entry in discovered_entries:
       module_name = entry.value
       # Cargar e importar de forma dinámica
   ```
   Esto permite a cualquier desarrollador de la comunidad registrar su add-on en el archivo `pyproject.toml` de su paquete. Al instalarlo vía `pip`, el visor lo descubrirá automáticamente de forma orgánica y sin modificar el core de MolSysViewer.

2. **Propagación y Reporte Interactivo de Fallas de Carga**:
   Cuando una importación falle dentro de `discover`, atrapar la excepción y registrar la traza detallada del error en una colección interna de fallas de inicialización (ej. `self._discovery_failures: dict[str, str]`).
   * Al renderizar el visor en Jupyter, si la colección contiene registros de fallas, presentar una alerta descriptiva no obstructiva en el lienzo o un botón de diagnóstico en el panel lateral:
     *"Warning: 1 add-on ('molsysviewer_elasnetmt') failed to load. Click here to view the Python traceback."*
   * Esto permite al desarrollador hacer clic en la UI para inspeccionar el traceback del error de importación directamente en el notebook.

---

## 4. Criterios de Aceptación

1. MolSysViewer debe descubrir de forma automática y orgánica add-ons externos instalados en el entorno de Python mediante puntos de entrada estándar (`entry_points`), eliminando la necesidad de mantener la tupla estática `KNOWN_ADDON_MODULES`.
2. Los errores de importación y fallas de inicialización de add-ons ocurridos durante la fase de descubrimiento automático deben ser registrados y presentados de forma visible y descriptiva al usuario en la interfaz interactiva.
3. Se deben incorporar pruebas automatizadas que validen el registro y descubrimiento de add-ons dinámicos mediante puntos de entrada simulados en entornos de prueba aislados.
