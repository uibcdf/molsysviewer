# Propuesta de Mejora: Validación de Compatibilidad y Resolución de Conflictos de Add-ons

## 1. Contexto y Diagnóstico

MolSysViewer permite la extensibilidad interactiva mediante la carga de add-ons externos registrados en la clase `GlobalAddonsRegistry` en `molsysviewer/addons.py`. Cada add-on declara un objeto `AddonSpec` que contiene metadatos clave como `name`, `version`, `package` y las contribuciones que inyecta en el visor (paneles, herramientas, acciones contextuales).

El problema de robustez e integración radica en que **el cargador de add-ons no realiza validaciones de compatibilidad ni de colisión de nombres**:
1. **Ausencia de Chequeo de Compatibilidad**: Un add-on diseñado para una versión futura o con APIs incompatibles (ej. que requiera MolSysViewer >= 1.5.0) es cargado a ciegas por un visor antiguo (v1.0.0). Al interactuar con el panel, fallará de forma abrupta con excepciones crípticas en tiempo de ejecución.
2. **Colisión de Identificadores**: No existe un mecanismo para resolver conflictos si dos add-ons del entorno intentan registrar el mismo `id` de panel o inyectar el mismo nombre en el espacio de nombres de la vista (`view.addons.<addon_name>`). La última importación sobrescribirá silenciosamente a la anterior, provocando comportamientos no reproducibles.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Inestabilidad Críptica**: Los usuarios experimentan bloqueos y tracebacks complejos en sus celdas de Jupyter al instalar actualizaciones de add-ons sin saber que su versión central de MolSysViewer ha quedado obsoleta para soportarlos.
* **Comportamiento Impredecible**: La sobrescritura silenciosa de espacios de nombres por colisión de identificadores rompe el determinismo y la reproducibilidad de los flujos de modelado, haciendo que el comportamiento del visor dependa del orden arbitrario en que Python importó los módulos en el entorno.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

Se propone dotar al cargador de add-ons de un esquema de validación de metadatos semánticos y políticas de prevención de colisiones:

1. **Introducir Compatibilidad de Versiones Semánticas (Semantic Versioning)**:
   Añadir el campo `requires_molsysviewer` en la definición de `AddonSpec` para declarar dependencias de versión explícitas:
   ```python
   # En AddonSpec
   requires_molsysviewer: str | None = None  # ej. ">=1.1.0, <2.0.0"
   ```
   Durante la fase de registro (`GlobalAddonsRegistry.register(...)`), el cargador debe validar de forma temprana la versión del visor frente al requerimiento del add-on (por ejemplo, utilizando la librería `packaging.specifiers`). Si no es compatible, abortar el registro de forma segura emitiendo una advertencia clara en el kernel.

2. **Detección Estricta de Colisiones de Identificadores**:
   Modificar el registro para evitar la sobrescritura silenciosa. Si un add-on intenta registrar un identificador ya ocupado:
   * **Rechazar por Defecto**: Lanzar una excepción de registro explícita (`ValueError: Add-on namespace 'elasnetmt' is already registered.`) para alertar de forma temprana al desarrollador en el entorno de Jupyter.
   * **Ofrecer Mecanismo de Alias**: Permitir al desarrollador instanciar o habilitar el add-on bajo un alias único en caliente para resolver la colisión si es necesario.

---

## 4. Criterios de Aceptación

1. El registro de un add-on cuyos requisitos de versión de MolSysViewer no sean compatibles con la versión instalada actualmente debe ser rechazado de forma temprana, emitiendo un reporte explicativo en el kernel.
2. Intentar registrar un add-on con un nombre o identificador que ya se encuentra en uso por otra extensión activa debe lanzar una excepción explícita en Python, evitando la sobrescritura silenciosa de namespaces en `view.addons`.
3. Se deben incorporar pruebas unitarias que evalúen el comportamiento del cargador al ser alimentado con add-ons de versiones incompatibles o con identificadores duplicados, garantizando la estabilidad y predictibilidad del sistema.
