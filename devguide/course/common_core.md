# El Tronco Común (Common Core) de MolSysViewer

El **Tronco Común** es la columna vertebral del Master Course de MolSysViewer. Su objetivo principal es llevar a un usuario desde los conceptos más básicos de inicialización e interacción gráfica en el lienzo 3D hasta la maestría de la manipulación de coordenadas moleculares y la automatización programática de la visualización reproducible.

---

## 🎯 1. Objetivos del Proyecto

El tronco común está diseñado para que cualquier estudiante logre:
1.  **Garantizar la reproducibilidad:** Escribir scripts en Python que recreen con precisión milimétrica cualquier escena molecular construida interactivamente.
2.  **Dominar la jerarquía visual:** Aprender a usar los constructos de `whole`, `regions`, `selections` y `layers` para controlar la densidad visual de sistemas biomoleculares complejos.
3.  **Hacer análisis cuantitativo seguro:** Extraer mediciones espaciales integradas con PyUnitWizard para mantener la consistencia física dimensional.
4.  **Manipular coordenadas y topologías:** Modificar posiciones espaciales de los átomos en Python y sincronizar la vista 3D sin romper anotaciones, capas ni mediciones.

---

## 💡 2. Pilares Pedagógicos

El diseño del contenido sigue tres principios fundamentales:
*   **Ciencia primero:** Cada unidad se abre con un "Hook Científico" (ej. *"¿Cómo identificamos y resaltamos los aminoácidos de una cavidad activa?"*) para justificar la necesidad del código que se va a enseñar.
*   **La acción y su eco programático:** El curso se divide en emparejar la comodidad del clic en el lienzo (UX interactiva) con su equivalente exacto en Python (API programática).
*   **Diagnóstico integrado:** Se enseña al estudiante a auditar de manera constante el estado interno de la memoria (`view.info()`, `smonitor.report()`) para resolver inconsistencias.

---

## 🗺️ 3. Estructura de las 27 Unidades

El proyecto se compone de las siguientes unidades secuenciales ubicadas en el directorio [sandbox/Curso/](../../sandbox/Curso/):

1.  **El Widget Molecular y Layouts:** Inicializar el visualizador en Jupyter y personalizar layouts.
2.  **Primera Carga y Metadatos:** Cargar estructuras en bruto e inspeccionar bloques de carga.
3.  **Caja de Simulación y Proyecciones:** Visualizar celdas unitarias y alternar proyecciones de cámara.
4.  **Carga Aditiva (Multi-sistema):** Agregar múltiples sistemas moleculares independientes en una escena.
5.  **Selección Interactiva (UX):** Capturar y procesar clics atómicos desde el lienzo.
6.  **Selección Programática:** Usar el motor MolSysMT para definir conjuntos de átomos.
7.  **El Registro de Selecciones:** Guardar, nombrar y recuperar selecciones.
8.  **Whole vs Regions:** Estructurar la jerarquía visual entre el fondo y grupos atómicos.
9.  **Representaciones Manuales:** Ajustar granularmente estilos gráficos y transparencias (`alpha`).
10. **Presets y Estilos Inteligentes:** Aplicar configuraciones de visualización rápidas y presets YAML.
11. **Esquemas de Color Categóricos:** Colorear según cadenas, elementos o estructura secundaria.
12. **Mapeo Cuantitativo de Color:** Pintar gradientes continuos a partir de arrays numéricos.
13. **Cámara y Puntos de Vista:** Guardar e invocar instantáneas estables de la cámara.
14. **Anotaciones de Texto:** Agregar etiquetas de texto 3D fijas ancladas a átomos.
15. **Medidas de Precisión:** Obtener distancias, ángulos y diedros unitariamente seguros.
16. **Figuras Geométricas Abstractas:** Crear esferas, cilindros o flechas de dirección artificiales.
17. **Organización por Capas (Layers):** Agrupar objetos y alternar visibilidades en masa.
18. **Tiempo y Trayectorias:** Controlar dinámicas moleculares de múltiples estructuras en el reproductor.
19. **Clipping y Sección de Planos:** Utilizar planos de corte interactivos mediante Gizmos.
20. **Extracción y Clonación:** Separar regiones del sistema o duplicar la sesión de visualización.
21. **Fusión y Alineación:** Superponer y alinear sistemas espacialmente combinando visores.
22. **El Motor de Datos (MolSysMT):** Consultar y analizar la topología mediante el backend.
23. **Ingeniería de Coordenadas:** Manipular arrays de coordenadas en Python y subirlos al visor.
24. **Reconstrucción Topológica:** Modificar la topología del sistema molecular reconciliando los índices.
25. **Infraestructura de Add-ons:** Descubrir, habilitar y comunicarse con plugins científicos externos.
26. **Forense y Diagnóstico:** Auditar señales con SMonitor y la consola de JavaScript.
27. **Exportables Profesionales:** Crear figuras estables con FigureSpec e interactivos HTML independientes.
