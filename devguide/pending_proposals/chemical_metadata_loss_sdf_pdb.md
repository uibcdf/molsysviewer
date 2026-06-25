# Propuesta de Mejora: Preservación de Metadatos Químicos (SDF/MOL2 a Mol*)

## 1. Contexto y Diagnóstico

MolSysViewer está diseñado para interactuar con sistemas moleculares que van desde macromoléculas biológicas (proteínas, ácidos nucleicos) hasta pequeños ligandos orgánicos y fármacos. Cuando se carga una molécula pequeña en formato de archivo químico estándar (como **SDF** o **MOL2**), la topología se parsea en Python a través del ecosistema MolSysMT.

El problema conceptual de visualización radica en la **frontera de transferencia de formatos hacia el frontend**:
1. El motor de visualización Mol* está históricamente optimizado para formatos macromoleculares (MMCIF, PDB).
2. Para simplificar el canal de transmisión de datos, MolSysViewer convierte el sistema de moléculas pequeñas en Python en un bloque de texto en **formato PDB sintético** y lo envía al frontend para que Mol* lo renderice.
3. El formato PDB es intrínsecamente limitado y **carece de soporte para metadatos químicos críticos**: no puede almacenar órdenes de enlace complejos (dobles enlaces, enlaces aromáticos o triples), cargas formales de los átomos, ni metadatos y propiedades personalizadas asociadas al archivo SDF (ej. campos de texto del SDF).
4. Como consecuencia directa, Mol* renderiza el ligando orgánico utilizando **enlaces sencillos genéricos** en la escena 3D, y se pierden por completo las propiedades químicas del archivo original para inspección interactiva.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Baja Fidelidad Científica**: Para los químicos medicinales y computacionales, visualizar una molécula con órdenes de enlace incorrectos (por ejemplo, ver un anillo de benceno representado con enlaces sencillos sin deslocalización aromática, o un grupo carbonilo sin su doble enlace $C=O$) es científicamente inaceptable y dificulta la inspección rápida de complementariedades geométricas y electrónicas en el sitio activo.
2. **Pérdida de Contexto de Docking**: Al visualizar resultados de cribado virtual (virtual screening), los científicos pierden el acceso visual a metadatos clave almacenados en el archivo SDF (como puntuaciones de docking, energías de interacción o identificadores de base de datos del ligando), los cuales deberían poder mostrarse de forma interactiva al cruzar el cursor sobre la molécula o en los paneles de add-on.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Transmisión y Carga Nativa de Formato SDF/MOL2 en Mol*

Se propone rediseñar el cargador y canal de datos de ligandos químicos en el visualizador:

1. **Utilizar el Lector SDF Nativo de Mol***:
   Mol* cuenta con un parser nativo extremadamente robusto para archivos en formato SDF (formatos químicos estructurados). En lugar de forzar la conversión asimétrica "SDF -> PDB sintético -> Mol*" en Python, el cargador de MolSysViewer en Python debe empaquetar y enviar el archivo SDF **en su formato crudo nativo** como una cadena de texto (o codificado en base64 si es necesario) hacia el frontend.
   
2. **Habilitar el Bloque de Inicialización SDF en JS**:
   Modificar el cargador en `viewer-controller.ts` para que, al detectar que la estructura es una molécula pequeña o proviene de un formato químico, invoque al cargador nativo de SDF de Mol*:
   ```typescript
   // En el frontend de JS, inicializar usando el parser de SDF de Mol*
   const data = await this.plugin.builders.data.rawData({ data: sdfText });
   const trajectory = await this.plugin.builders.structure.parseTrajectory(data, 'sdf');
   ```
   * Mol* calculará y dibujará de forma nativa la geometría tridimensional respetando con precisión absoluta los órdenes de enlace dobles, triples y aromáticos descritos en la tabla de conectividad del SDF.

3. **Exponer Propiedades del SDF en los Eventos de Interacción**:
   El lector nativo de Mol* extraerá las propiedades del archivo SDF y las adjuntará al modelo. El normalizador de eventos en `viewer-controller.ts` podrá entonces capturar estos metadatos y enriquecer los payloads de interacción (hover, click) con la información química y de docking, enviándola directamente a los paneles de add-on y de vuelta a Python.

---

## 4. Criterios de Aceptación

1. Los ligandos orgánicos y moléculas pequeñas cargados en formato SDF o MOL2 deben renderizarse en el lienzo 3D de MolSysViewer respetando fielmente los órdenes de enlace correctos (dobles, triples y aromáticos) de la estructura.
2. El usuario debe poder inspeccionar y consultar los metadatos y propiedades personalizadas del archivo SDF a través de las APIs de interacción en Python y en los add-ons laterales.
3. Se deben incorporar pruebas de visualización y regresión que convaliden que la carga de formatos químicos no destruye la información de conectividad fina ni los órdenes de enlace moleculares.
