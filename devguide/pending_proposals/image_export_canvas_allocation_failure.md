# Propuesta de Mejora: Robustez en Exportación de Imágenes (Prevenir Límites de GPU MAX_RENDERBUFFER_SIZE)

## 1. Contexto y Diagnóstico

MolSysViewer proporciona una potente funcionalidad de exportación de imágenes y figuras de alta resolución orientadas a publicaciones científicas a través de `ExportManager` en `molsysviewer/exports.py`. Los métodos `view.export.image()` y `view.export.figure()` permiten especificar el ancho (`width_px`), el alto (`height_px`) y un factor de multiplicación de escala (`scale`), por ejemplo, una escala de `2.0` o `4.0`.

El backend de Python delega la exportación al frontend enviando un mensaje `request_image_export`. En el frontend, Mol* redimensiona dinámicamente el lienzo (`HTMLCanvasElement`) o crea un buffer de renderizado virtual con las dimensiones multiplicadas (`width * scale` por `height * scale`) para generar una imagen de alta densidad de píxeles (ej. 300 o 600 DPI para revistas como *Nature* o *Science*).

El fallo crítico radica en que **el visor no valida si las dimensiones virtuales resultantes superan los límites físicos de hardware de la GPU del usuario**:
* La especificación WebGL y las GPU modernas definen límites físicos como `gl.MAX_RENDERBUFFER_SIZE` y `gl.MAX_VIEWPORT_DIMS` (típicamente `8192` o `16384` píxeles).
* Si un investigador solicita una figura con dimensiones de `4000x3000` y una escala de `4.0`, la resolución virtual resultante es de `16000x12000` píxeles, lo cual requiere cerca de **768 MB de memoria de video contigua** para almacenar los píxeles sin comprimir.
* Si estas dimensiones superan los límites de la GPU, el navegador experimenta un fallo silencioso al redimensionar, o WebGL lanza un error de falta de memoria (Out-of-Memory), lo cual desencadena un **evento catastrófico de pérdida de contexto de WebGL (`webglcontextlost`)**, destruyendo el visor por completo y forzando al usuario a reiniciar la sesión.
* En Python, el bucle de espera activa en `_request_image_export` se queda colgado esperando la respuesta hasta que alcanza el tiempo de espera (`timeout_s`), arrojando un error genérico `RuntimeError: Frontend image export did not return a PNG data URI` o escribiendo una imagen completamente en blanco (negra o transparente) sin dar explicaciones científicas sobre el límite excedido.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Inestabilidad del Entorno de Trabajo**: El intento de exportar una figura de alta resolución para un artículo científico puede provocar la pérdida total del trabajo en curso en la sesión de Jupyter al bloquearse el contexto gráfico WebGL.
* **Falta de Diagnóstico Claro**: El usuario recibe una imagen vacía o un error de timeout genérico, sin saber si el problema es de su código, de la librería, del navegador o de las limitaciones físicas de su tarjeta gráfica.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Pre-verificación de Límites WebGL en el Frontend
Se propone implementar un mecanismo de validación y control de errores robusto antes de iniciar la asignación de memoria para el canvas de exportación:

1. **Consulta de Parámetros WebGL**:
   Antes de aplicar el cambio de tamaño del canvas en el frontend, el controlador de exportación de MolSysViewer en TypeScript/JavaScript debe interrogar al contexto WebGL sobre sus límites reales:
   ```typescript
   const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
   if (gl) {
       const maxRenderBufferSize = gl.getParameter(gl.MAX_RENDERBUFFER_SIZE);
       const maxViewportDims = gl.getParameter(gl.MAX_VIEWPORT_DIMS); // [width, height]
       
       const targetWidth = width * scale;
       const targetHeight = height * scale;
       
       if (targetWidth > maxRenderBufferSize || targetHeight > maxRenderBufferSize) {
           // Supera los límites físicos de WebGL
           return {
               success: false,
               error_type: "GPU_LIMIT_EXCEEDED",
               message: `Requested dimensions (${targetWidth}x${targetHeight}) exceed the GPU maximum renderbuffer size of ${maxRenderBufferSize}px.`
           };
       }
   }
   ```

2. **Propagación y Manejo del Error en Python**:
   Si la validación del frontend falla, debe responder inmediatamente al backend de Python enviando un evento de error. El backend intercepta este mensaje, interrumpe el bucle de espera activa de forma inmediata (evitando esperar inútilmente el timeout de 2 segundos) y lanza un `ValueError` claro y descriptivo al usuario:
   ```python
   # En Python, al recibir el evento de error de la GPU:
   raise ValueError(
       f"No se pudo exportar la imagen: las dimensiones solicitadas ({width_px * scale}x{height_px * scale} px) "
       f"superan el límite físico de su tarjeta gráfica (máximo permitido: {max_limit} px). "
       f"Por favor, reduzca el ancho/alto o disminuya el factor de escala (ej. scale=2.0)."
   )
   ```

---

## 4. Criterios de Aceptación

1. El intento de exportar una imagen con dimensiones excesivas no debe provocar la pérdida de contexto de WebGL ni colapsar el visor molecular interactivo.
2. Si el tamaño solicitado supera los límites de hardware de la GPU del usuario, la librería debe fallar de forma controlada e instantánea (sin esperar los 2 segundos de timeout), informando al usuario mediante un mensaje de error claro en Python con recomendaciones de ajuste.
3. Se deben añadir pruebas unitarias/E2E que verifiquen el comportamiento de la librería ante dimensiones fuera de límites simuladas, garantizando que el visor sigue respondiendo perfectamente después de rechazar la petición de exportación.
