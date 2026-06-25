# Propuesta de Mejora: Validación y Control de Límites de Hardware en Exportación de Imágenes

## 1. Contexto y Diagnóstico

MolSysViewer proporciona una API potente en Python para exportar imágenes tridimensionales de alta resolución en disco (`view.scene.export_image(...)` y los métodos en `molsysviewer/viewer/export.py`). El usuario puede especificar dimensiones personalizadas (ancho y alto en píxeles) o factores de escala para obtener imágenes nítidas destinadas a publicaciones científicas.

El problema operativo radica en que **la exportación de imágenes depende estrictamente de las limitaciones físicas del buffer WebGL de la GPU del usuario**:
1. Los navegadores web y los entornos WebGL imponen un tamaño máximo para el buffer de renderizado (típicamente de 4096px o 8192px de ancho/alto en la mayoría de hardware estándar, y excepcionalmente 16384px en GPUs de gama alta).
2. Si el usuario solicita exportar una imagen con dimensiones masivas que superan este límite (ej. `view.scene.export_image(width=12000, height=8000)`), el motor de Mol* en el navegador fallará silenciosamente al intentar inicializar un canvas de renderizado fuera de los límites físicos soportados por la GPU.
3. El resultado de la exportación es una **imagen completamente en blanco (vacía), truncada o corrupta**, sin que el backend de Python realice validaciones previas o informe al usuario sobre la causa de la falla.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Pérdida de Tiempo y Frustración**: Los científicos intentan generar figuras de ultra-alta resolución para revistas científicas de prestigio y se encuentran con archivos guardados de 0 bytes o imágenes en negro con fondo transparente. Al no recibir advertencias, asumen de forma errónea que existe un bug en el visor o en el formato de guardado de Python.
2. **Inconsistencia entre Plataformas**: Un script de exportación que funciona perfectamente en la estación de trabajo local (con una GPU potente) fallará de forma silenciosa al ejecutarse en una laptop delgada o en un entorno de nube con aceleración por software básica.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Consulta de Capacidades WebGL y Re-escalado Automático Seguro

Se propone robustecer el flujo de exportación de imágenes incorporando validaciones de hardware dinámicas:

1. **Consultar Límites de la GPU al Iniciar**:
   Durante la fase de inicialización (`ready` en `viewer-controller.ts`), el frontend de JavaScript debe consultar las capacidades máximas del contexto de WebGL/WebGPU del navegador:
   ```javascript
   const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
   const maxRenderBufferSize = gl ? gl.getParameter(gl.MAX_RENDERBUFFER_SIZE) : 4096;
   // Enviar este límite físico como parte de los metadatos de liveness a Python
   ```

2. **Validación y Alertas en el Backend (Python)**:
   Al recibir la petición de exportación en `export.py`, el backend debe comparar las dimensiones solicitadas con el límite `max_renderbuffer_size` reportado por el navegador. Si el tamaño solicitado supera el límite físico de la GPU activa:
   * **Re-escalar Automáticamente**: Ajustar proporcionalmente el ancho y el alto para encajar exactamente en el límite máximo de la GPU.
   * **Advertir al Usuario**: Emitir una advertencia científica de Python (`UserWarning`) informando sobre el ajuste forzado:
     *"Requested image dimensions [12000x8000] exceed the maximum GPU renderbuffer size of [8192]. Automatically downscaling image to [8192x5461] to prevent black-screen export."*

3. **Manejo de Errores de Asignación en JS**:
   Si a pesar de las validaciones el navegador falla al crear el canvas de exportación, el frontend debe atrapar el error e informar al backend para propagar una excepción descriptiva (`RuntimeError: GPU failed to allocate drawing buffer for export`).

---

## 4. Criterios de Aceptación

1. Las llamadas a `export_image` con dimensiones fuera de los límites físicos de la GPU no deben generar archivos corruptos, vacíos o imágenes en negro de forma silenciosa.
2. La librería debe detectar dinámicamente el límite `MAX_RENDERBUFFER_SIZE` del hardware activo y ajustar o advertir al usuario antes de proceder con el renderizado de exportación.
3. Se deben añadir pruebas de robustez que convaliden que la exportación de imágenes maneja con gracia los límites extremos de resolución en diferentes perfiles de hardware simulados.
