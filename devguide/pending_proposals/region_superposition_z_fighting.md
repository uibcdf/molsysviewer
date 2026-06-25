# Propuesta de Mejora: Composición Espacial y Resolución de Superposiciones en Regiones

## 1. Contexto y Diagnóstico

En MolSysViewer, las regiones (`Region` en `molsysviewer/regions.py`) permiten agrupar selecciones de átomos y aplicarles estilos o representaciones gráficas independientes. Cada región se traduce en el frontend a un componente autónomo en el árbol de estado de Mol*.

El problema conceptual de composición radica en que **las regiones son tratadas como entidades visualmente aisladas**. Si un usuario define múltiples regiones que comparten un conjunto de átomos (intersección) y les aplica representaciones visuales distintas (por ejemplo, `cartoon` en la región `R1` y `ball-and-stick` en la región `R2` sobre la misma cadena de aminoácidos):
1. El motor gráfico Mol* renderiza ambas representaciones geométricas superpuestas en el mismo espacio tridimensional.
2. Esto provoca artefactos visuales severos (como el parpadeo de texturas o *z-fighting* en la GPU debido a la coincidencia exacta de coordenadas en los buffers de dibujo).
3. No existe en la librería un modelo de relaciones espaciales ni de composición para gestionar o prevenir estas superposiciones de forma automatizada.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Degradación de la Calidad Visual**: Las superposiciones accidentales de mallas pesadas y cintas generan escenas confusas y de baja calidad estética, dificultando la interpretación de interacciones ligando-proteína.
2. **Carga Innecesaria en la GPU**: Renderizar múltiples geometrías redundantes sobre los mismos átomos reduce el rendimiento (FPS) del visor en sistemas macromoleculares masivos.
3. **Fricción de Modelado**: Obliga al usuario a realizar cálculos manuales complejos en Python (utilizando operaciones lógicas de MolSysMT sobre listas de índices de átomos) para restar o excluir átomos de sus selecciones y poder aplicar estilos limpios.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Operaciones Booleanas de Composición y Advertencia de Superposición

Se propone dotar al gestor de regiones (`RegionsManager`) de capacidades de álgebra espacial:

1. **Operaciones Booleanas entre Regiones en Python**:
   Habilitar métodos de composición lógica en la API pública para generar nuevas regiones a partir de las existentes:
   * **Diferencia (`difference` / operador `-`)**: `R3 = R1 - R2` (crea una región con los átomos de `R1` excluyendo los de `R2`).
   * **Intersección (`intersection` / operador `&`)**: `R3 = R1 & R2` (crea una región que solo contiene los átomos comunes).
   * **Unión (`union` / operador `|`)**: `R3 = R1 | R2` (combina ambas selecciones en un componente unificado).
   
   *Ejemplo de flujo simplificado*:
   ```python
   # Crear regiones
   r_sol = view.regions.new("solvente", selection="water")
   r_site = view.regions.new("sitio_activo", selection="within 5.0 of ligand")
   
   # Resolver superposición restando el solvente del sitio activo
   r_clean_site = r_site - r_sol
   r_clean_site.set_representation("licorice")
   ```

2. **Detección y Advertencias de Superposición (Overlap Warning)**:
   Añadir una validación en `RegionsManager.new()` que compute si la nueva región intersecta átomos de regiones ya existentes con representaciones visibles activas. Si se detecta una intersección, emitir una advertencia científica de Python (`UserWarning`) informando sobre la superposición y los tags de las regiones afectadas para que el usuario pueda tomar una decisión consciente.

---

## 4. Criterios de Aceptación

1. La API de `view.regions` debe admitir operaciones de composición booleana (diferencia, intersección, unión) retornando objetos `Region` funcionales y reproducibles.
2. La creación de una región que se superponga con otra región visible activa debe notificar al usuario mediante una advertencia clara sin interrumpir el flujo de ejecución.
3. Se deben incorporar pruebas unitarias que validen la precisión de los índices resultantes tras aplicar operaciones booleanas sobre regiones del sistema demo.
