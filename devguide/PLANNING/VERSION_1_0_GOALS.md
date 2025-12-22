# MolSysViewer — Objetivos versión 1.0

Este documento recoge de forma explícita y detallada los objetivos para la
versión **1.0** de MolSysViewer. La idea es cristalizar la **ruta inmediata**
para pasar de un prototipo avanzado a un visor estable, coherente y cómodo de
usar y mantener.

La versión 1.0 se apoya en la arquitectura actual (Python + anywidget + Mol\*)
que ya está implementada, y se centra en **consolidar** esa base:

- cerrar huecos de comportamiento y tests,
- definir claramente la API pública,
- pulir la experiencia de usuario (incluido el popup),
- y alinear documentación, devguide y código.

No introduce todavía nuevas familias grandes de APIs científicas (`get_*`,
`show_*` avanzados); esas se reservan para 2.0.

---

## 1. Visión general de la 1.0

La 1.0 debe ser, sobre todo, una versión:

- **estable**: comportamiento predecible y consistente en carga, regiones,
  capas, popup, trayectorias y shapes básicos;
- **bien definida**: API pública clara (`MolSysView`, loaders, shapes,
  regiones/layers/whole (global), popup) y documentada;
- **confiable en notebooks y docs**: buen funcionamiento en Jupyter,
  exportación HTML sólida, ejemplos reproducibles;
- **mantenible**: código y documentación alineados, con tests suficientes para
  evitar regresiones triviales al evolucionar hacia 2.0.

La arquitectura base no se cambia; se refina.

---

## 2. Alcance funcional mínimo de la 1.0

### 2.1. Carga de estructuras

Para 1.0, los caminos de carga deben considerarse “cerrados” y bien probados:

- `MolSysView.load(molecular_system, ...)` basado en **MolSysMT**:
  - Conversión a `molsysmt.MolSys`.
  - Generación robusta del payload `MolSysPayload` a partir de `ViewerJSON`.
  - Manejo de enlaces (`bonds`), coordenadas, cajas (`box`) y tiempos.

- Loaders específicos:
  - `load_pdb_string`, `load_mmcif_string`:
    - Construyen `_molsys` y máscaras (`atom_mask`) coherentes.
    - Envían correctamente `load_structure_from_string`.
  - `load_pdb_id`:
    - Usa MolSysMT para `_molsys` y `atom_mask`.
    - Normaliza el ID PDB y delega la descarga en Mol\* (`load_pdb_id`).
  - `load_from_url`:
    - Documentar explícitamente que delega en Mol\* y que no construye
      `_molsys` ni permite selecciones Python, para evitar confusiones.

Objetivo 1.0: **todos estos caminos deben estar cubiertos por tests y
documentación clara**, incluyendo ejemplos simples de uso en docs.

### 2.2. Regiones, capas y vista whole (global)

El sistema `regions/layers/whole` ya existe, pero la 1.0 debe asegurar que:

- API Python:
  - `new_region`, `new_layer`, `regions`, `layers`, `whole`.
  - Métodos de `Region`: `set_representation`, `show`, `hide`, `delete`,
    `new_complementary_region`.
  - Métodos de `Layer`: `show`, `hide`, `delete`, `set_tag`.
  - `Whole`: `set_representation`, `show`, `hide`.

- Semántica clara (y documentada) de visibilidad:
  - `show/hide/isolate` en el viewer afectan máscaras y reps globales.
  - `region.hide()` no se “pierde” al hacer `viewer.hide(); viewer.show()`.
  - `whole.hide()` se respeta aunque se llame antes del primer `show()`.

- Complementos:
  - Funcionan de forma robusta cuando hay múltiples regiones con
    `atom_indices` conocidos (a través de `region_ack`).
  - Los errores se comunican de manera clara (ej. no hay sistema cargado,
    regiones sin `atom_indices`, etc.).

Objetivo 1.0: que el comportamiento descrito en `REGIONS_LAYERS.md` y
checkpoints esté plenamente reflejado en tests (Python y, en lo posible, JS)
y en ejemplos de usuario.

### 2.3. Shapes científicos básicos

Las shapes más importantes para 1.0 son:

- Esferas (`add_sphere`, `add_spheres`, `add_set_alpha_spheres`).
- Superficies de pocket / blobs.
- Tubos de canal (`add_channel_tube`).
- Elementos farmacofóricos básicos (tal como se haya implementado ya).

Objetivos para 1.0:

- Asegurar que las firmas Python están claras (tipos, defaults, comportamiento
  en broadcasting de parámetros).
- Garantizar que las shapes se vinculan a capas (`Layer`) coherentes y
  que `hide_layer/show_layer/delete_layer` funcionan aunque haya mensajes
  encolados o delays.
- Mantener los mensajes TS (`ViewerMessage`) en sync con las expectativas de
  Python (tests que validen la forma de los diccionarios).
No se trata de añadir nuevas primitives para 1.0, sino de **cerrar bien
las existentes**.

### 2.4. Popup (ventana espejo)

Para 1.0, el popup debe considerarse una característica “de primera clase”:

- Comportamiento esperado:
  - Botón `Pop` en el host abre una ventana con el mismo viewer.
  - El popup reproduce el historial de comandos (load, shapes, regiones,
    etc.) y el snapshot de cámara inicial.
  - Los controles (Reset/Full/Bg/Spin/Swing + trayectoria) funcionan en el
    popup igual que en el host.
  - La cámara se sincroniza host↔popup sin “pelea”, respetando interacciones
    del usuario en cada lado.

- Aspectos técnicos:
  - Uso de `Blob` + `import` para cargar `viewer.js` en el popup.
  - Mensajes `molsysviewer-pop-ready`, `molsysviewer-initial-sync`,
    `molsysviewer-sync-op`, `molsysviewer-sync-camera`,
    `molsysviewer-sync-autohide`.

- Objetivo 1.0:
  - Confirmar la robustez del flujo (tests manuales bien documentados,
    E2E si es viable).
  - Documentar limitaciones de seguridad (uso de `postMessage("*")`) y
    escenarios recomendados (Jupyter local, docs, etc.).

### 2.5. Controles de trayectoria

Los controles de trayectoria (botones ±, slider, FPS/step, play/pause)
forman parte de la experiencia base.

Objetivos concretos 1.0:

- Garantizar que `TrajectoryHandlers` funciona bien con trayectorias cortas
  y medianas (y se comporta de forma razonable si sólo hay 1 frame).
- Propagar el estado de reproducción (`isPlaying`, `currentFrame`,
  `frameCount`) al UI de forma coherente host/popup.
- Cubrir al menos un flujo de trayectoria con tests (Python + JS o E2E) que
  detecten regresiones obvias.

---

## 3. Estabilización de arquitectura y protocolo

Además de funcionalidades, la 1.0 debe “congelar” la arquitectura en ciertos
aspectos:

- **MolSysPayload**:
  - Confirmar y documentar como contrato estable:
    - `atoms` (columnas principales).
    - `structures` (lista de frames con `coordinates` en Å, `box` y `time`).
    - `bonds`.
    - `time` global opcional (delta/offset/unit).

- **Mensajes Python↔TS**:
  - Asegurar que `ViewerMessage` refleja todos los `op` reales.
  - Documentar brevemente las operaciones clave (carga, visibilidad,
    regiones, capas, whole (global), trayectoria, popup) en devguide.

- **Inicialización Mol\***:
  - Mantener usos correctos de `PluginContext` (`init()`, `initViewer` o
    `initViewerAsync`) y dejarlo anotado en devguide para futuras refactors.

Objetivo 1.0: que no haga falta “adivinar” cómo están definidos estos
contratos; que queden claros en el devguide y sean difíciles de romper
accidentalmente.

---

## 4. Calidad: tests y mantenimiento

La 1.0 no exige cobertura perfecta, pero sí:

- Cobertura razonable de:
  - Loaders (MolSysMT, PDB/mmCIF, PDB ID, URL).
  - Regions/layers/whole (incluyendo complementos y visibilidad).
  - Shapes clave (esferas, pockets, tubos) a nivel de mensajes Python.
  - Exportación HTML (`write_html` en modo standalone/docs).

- Al menos un camino JS/TS probado:
  - Unitario (`region-hide.test.ts` y análogos) para la lógica de estado
    (hide/show de regiones, visibilidad).
  - E2E mínimo con Playwright que cargue estructura, cree región y la
    oculte sin errores de consola ni WebGL (como ya existe, reforzándolo si
    hace falta).

- Mantenimiento:
  - Asegurar que cada cambio relevante en arquitectura se refleja en:
    - devguide (`STRUCTURE`, `DESIGN/ARCHITECTURE`, checkpoints).
    - `ROADMAP.md` (marcar hitos de 1.0).

---

## 5. Experiencia de usuario y documentación

Una parte clave de la 1.0 es que la gente pueda **entender y usar** el
visor sin tener que leer el código.

Objetivos:

- **Flujos de usuario claros**:
  - Cargar estructuras con MolSysMT y con strings.
  - Crear regiones (posiblemente complementarias) y estilos.
  - Añadir overlays de shapes (esferas, pockets, tubos…) con tags y manejarlos
    por capa.
  - Usar el popup y los controles de trayectoria.
  - Exportar vistas HTML y embeberlas en docs.

- **Docs de desarrollador sólidas**:
  - Devguide actualizado (ya en marcha): arquitectura real, repositorio,
    payload, popup, regions/layers/whole.
  - Guía de contribución alineada con la estructura actual (paths reales,
    build TS manual, checkpoints en `HISTORY/`).

---

## 6. Resumen de entregables de la 1.0

En resumen, la versión 1.0 debe entregar:

- Un visor que:
  - carga estructuras (MolSysMT, PDB, mmCIF, URL) de forma predecible,
  - gestiona regiones, capas y representación global de forma robusta,
  - ofrece un popup sincronizado usable en notebooks,
  - maneja trayectorias con controles simples,
  - dispone de shapes científicos básicos útiles para TopoMT/PharmacophoreMT.

- Una arquitectura y un protocolo:
  - bien definidos en devguide,
  - razonablemente cubiertos por tests,
  - listos para soportar una evolución a 2.0 sin reescrituras profundas.

La 1.0 es, por tanto, la versión que “cierra el prototipo” y lo convierte en
una base sólida sobre la cual construir las capacidades avanzadas de la 2.0.
