# Guía de la Estructura del Master Course: Introducción a MolSysViewer

Este documento define la estructura oficial del tronco común del **Master Course de MolSysViewer** (Unidades 1 a 27). Cada unidad está diseñada bajo la filosofía de *"no dejar que la interacción supere a la reproducibilidad"*, conectando acciones interactivas en el lienzo 3D con sus equivalentes programáticos en Python.

---

## 🏗️ Estructura del Tronco Común (27 Unidades)

### Unidad 1: El Widget Molecular y Layouts
*   **Propósito:** Aprender a inicializar el visor dentro de entornos Jupyter y controlar la disposición de la interfaz.
*   **Conceptos Clave:** Inicialización del objeto `MolSysView`, configuración del lienzo visual, modos de interfaz (`controls_mode='classic'|'minimal'`), y organización de paneles y docking con `view.set_panel_mode()`.

### Unidad 2: Primera Carga y Metadatos
*   **Propósito:** Cargar la primera estructura molecular (PDB) en el visor y auditar la composición de la escena molecular.
*   **Conceptos Clave:** Uso de `view.load(..., mode='replace')`, inspección del registro de carga (`view.load_blocks`), y auditoría del estado del visor con `view.info()`.

### Unidad 3: Caja de Simulación y Proyecciones de Cámara
*   **Propósito:** Visualizar cajas de simulación/celdas unitarias y configurar la perspectiva técnica de la cámara.
*   **Conceptos Clave:** Renderizado de bordes de caja con `view.show_box()` y `view.hide_box()`, y cambio entre proyección ortográfica y perspectiva con `view.camera.set_mode()`.

### Unidad 4: Carga Aditiva (Multi-sistema)
*   **Propósito:** Cargar múltiples sistemas moleculares independientes en una misma sesión 3D de manera segura y sin colisiones de nombres.
*   **Conceptos Clave:** Carga múltiple con `view.load(..., mode='add')`, y comprensión del particionado lógico automático de regiones por cada bloque cargado.

### Unidad 5: Selección Interactiva (UX)
*   **Propósito:** Capturar e inspeccionar qué átomos o residuos ha seleccionado manualmente el usuario haciendo clic en la pantalla 3D.
*   **Conceptos Clave:** Monitoreo del estado en vivo con `view.active_selection`, métodos `is_empty()` y `clear()`, y consulta de eventos de interacción con `view.get_last_active_selection_event()`.

### Unidad 6: Selección Programática
*   **Propósito:** Utilizar el motor de selección de MolSysMT para definir subconjuntos de átomos mediante consultas de texto.
*   **Conceptos Clave:** Selección programática con `view.select()`, y sintaxis de consulta (ej. `backbone`, `sidechain`, `res_name "TYR"`, `within 5.0 angstroms of...`).

### Unidad 7: El Registro de Selecciones
*   **Propósito:** Guardar selecciones atómicas en un registro persistente con nombres personalizados (tags) para su reutilización.
*   **Conceptos Clave:** Almacenamiento en registro con `view.selections.add_selection()`, activación de selecciones guardadas con `.activate()`, foco de cámara con `.focus()`, y listado mediante `view.selections.tags`.

### Unidad 8: Whole vs Regions (Jerarquía Visual)
*   **Propósito:** Segmentar una estructura en unidades lógicas independientes para facilitar su manipulación visual.
*   **Conceptos Clave:** Uso del fondo de visualización global (`view.whole`), creación de regiones con `view.new_region(selection, tag)`, aislamiento visual con `view.isolate()`, y creación masiva automatizada con `view.make_regions_by()`.

### Unidad 9: Representaciones Manuales y Parámetros
*   **Propósito:** Aprender a definir la geometría visual detallada de las representaciones y controlar su opacidad.
*   **Conceptos Clave:** Estilos de renderizado (`cartoon`, `licorice`, `spacefill`), ajuste fino de radios y nivel de detalle, y control de transparencia con `alpha`.

### Unidad 10: Presets y Estilos Inteligentes
*   **Propósito:** Aplicar estilos preconfigurados complejos de Mol* y configurar recetas visuales del laboratorio a partir de archivos de configuración externos.
*   **Conceptos Clave:** Aplicación de recetas estándar de Mol* (`atomic-detail`, `polymer-cartoon`), y carga de recetas personalizadas de usuario en formato YAML (`load_user_presets()`).

### Unidad 11: Esquemas de Color Categóricos
*   **Propósito:** Colorear representaciones basándose en propiedades discretas o biológicas.
*   **Conceptos Clave:** Coloreo por cadena (`chain`), por tipo de elemento químico (`element`), y por estructura secundaria (`secondary-structure`) a través de la propiedad `color_scheme`.

### Unidad 12: Mapeo Cuantitativo de Color (Heatmaps)
*   **Propósito:** Visualizar propiedades cuantitativas continuas (ej. perfiles de fluctuación RMSF, accesibilidad al solvente SASA o conservación) directamente en la superficie molecular.
*   **Conceptos Clave:** Mapeo de listas numéricas con `view.whole.set_color_by_values()` y `region.set_color_by_values()`, uso de mapas de color de Matplotlib (ej. `viridis`), y restauración de colores por defecto con `reset_colors()`.

### Unidad 13: Cámara y Puntos de Vista Estables
*   **Propósito:** Controlar programáticamente el encuadre de la escena y almacenar instantáneas de cámara reproducibles.
*   **Conceptos Clave:** Enfoque automático con `camera.zoom()`, y captura/restauración de coordenadas de cámara mediante `view.camera.get_snapshot()` y `view.camera.set_snapshot()`.

### Unidad 14: Anotaciones de Texto (Etiquetas)
*   **Propósito:** Documentar la escena agregando etiquetas de texto tridimensionales flotantes ancladas a posiciones atómicas específicas.
*   **Conceptos Clave:** Inserción de textos con `view.annotations.add_annotation()`, etiquetas dinámicas con `add_label_from_active_selection()`, personalización de estilo (`color`, `size_em`, `background`), y operaciones de visualización (`show()`, `hide()`, `delete()`).

### Unidad 15: Medidas de Precisión
*   **Propósito:** Obtener valores geométricos precisos (distancias, ángulos y diedros) y recuperarlos como cantidades físicas con unidades reales.
*   **Conceptos Clave:** Creación de mediciones con `view.measurements.add_distance()`, `add_angle()`, `add_dihedral()`, y extracción de valores integrados con PyUnitWizard.

### Unidad 16: Figuras Geométricas Abstractas
*   **Propósito:** Dibujar objetos tridimensionales no atómicos en la escena para representar conceptos físicos (ej. centros de masas, esferas de exclusión, direcciones de fuerza).
*   **Conceptos Clave:** Creación de primitivas geométricas con `view.shapes.add_sphere()`, `add_links()`, y modificación dinámica de sus coordenadas.

### Unidad 17: Organización por Capas (Layers)
*   **Propósito:** Organizar y controlar el estado visual de múltiples objetos diversos (regiones, formas, etiquetas, medidas) de manera conjunta.
*   **Conceptos Clave:** Agrupación con `layer_tag`, e interrupción/activación masiva de visibilidad a través de la propiedad de colección `view.layers[layer_tag].hide()|show()`.

### Unidad 18: Tiempo y Trayectorias
*   **Propósito:** Cargar conjuntos de datos dinámicos provenientes de dinámicas moleculares y navegar en el tiempo de forma reproducible.
*   **Conceptos Clave:** Inicialización de trayectorias, manipulación del reproductor visual mediante la API `view.player`, salto a frames específicos con `go_to_structure(index)`, y control de reproducción (FPS, loops, step).

### Unidad 19: Clipping y Sección de Planos
*   **Propósito:** Cortar y seccionar visualmente densas proteínas o membranas para revelar sus estructuras internas y canales.
*   **Conceptos Clave:** Recortes de planos cercanos/lejanos de cámara con `scene.set_clip_planes()`, y adición de planos de sección en coordenadas del mundo mediante `scene.add_section()`, interactuando de forma limpia con los tiradores de arrastre Gizmo a través del objeto `Section`.

### Unidad 20: Extracción y Clonación Quirúrgica
*   **Propósito:** Aislar un subconjunto atómico o duplicar la sesión de visualización completa.
*   **Conceptos Clave:** Aislamiento de sistemas a nuevas instancias visuales independientes con `view.extract()`, y duplicación exacta de estados de sesión con `view.copy()`.

### Unidad 21: Fusión y Alineación Estructural (Superposición)
*   **Propósito:** Alinear espacialmente dos estructuras tridimensionales y componer múltiples visualizadores en uno solo.
*   **Conceptos Clave:** Alineación estructural mediante el backend con `msm.structure.align()`, y fusión de sesiones con `msv.tools.basic.merge()`.

### Unidad 22: El Motor de Datos (MolSysMT Integration)
*   **Propósito:** Acceder a la información topológica y realizar consultas analíticas complejas directamente en el backend de Python.
*   **Conceptos Clave:** Propiedad `view.molsys`, consultas complejas mediante funciones nativas de MolSysMT (`msm.get()`, `msm.select()`, `msm.info()`).

### Unidad 23: Ingeniería de Coordenadas
*   **Propósito:** Extraer arrays numéricos de coordenadas tridimensionales de los átomos, manipularlos en Python y actualizarlos dinámicamente en el visor.
*   **Conceptos Clave:** Lectura y escritura de coordenadas con `view.get_coordinates()` y `view.set_coordinates()`, y verificación de supervivencia de referencias en desplazamientos espaciales.

### Unidad 24: Reconstrucción Topológica (Edición Física)
*   **Propósito:** Modificar físicamente la topología del sistema molecular (ej. borrar moléculas de agua, realizar mutaciones en residuos) y reconciliar los índices de los elementos visuales creados.
*   **Conceptos Clave:** Edición del sistema mediante `view.apply_system_edit()`, re-mapeado automático de índices atómicos, y verificación de la supervivencia de etiquetas y mediciones pre-existentes tras la edición.

### Unidad 25: Infraestructura de Add-ons
*   **Propósito:** Ampliar las capacidades nativas del visor mediante la carga de plugins científicos externos.
*   **Conceptos Clave:** Descubrimiento de extensiones con `msv.addons.available()`, activación de complementos con `view.addons.enable()`, e invocación de cálculos especializados mediante `handle_context_action()`.

### Unidad 26: Forense y Diagnóstico (SMonitor & JS Logs)
*   **Propósito:** Auditar el rastro de señales internas del visualizador y resolver advertencias o errores silenciosos de renderizado.
*   **Conceptos Clave:** Obtención de informes de telemetría de SMonitor con `smonitor.report()`, activación del modo depuración con `debug_js=True`, e inspección del buffer de la consola JavaScript con `view.js_logs`.

### Unidad 27: Exportables Profesionales (Figuras e HTML)
*   **Propósito:** Generar imágenes de alta resolución aptas para publicaciones científicas y exportar la sesión 3D en formato HTML interactivo autocontenido.
*   **Conceptos Clave:** Uso de recetas reutilizables `FigureSpec`, renderizado por lotes, exportación interactiva con `view.export.html(mode='standalone'|'lite')`, y exportación de imágenes fijas con `view.export.image()`.
