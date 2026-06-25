# Propuesta de Mejora: Gestión de Fricción de Unidades en APIs Visuales (nm vs. Å)

## 1. Contexto y Diagnóstico

MolSysViewer está diseñado para integrarse estrechamente con MolSysMT, adoptando el estándar de la suite de trabajar internamente en **nanómetros (nm)** para todas las magnitudes de longitud. Por otro lado, el motor gráfico Mol* y los archivos estructurales tradicionales (PDB, MMCIF) operan de forma universal en **Angstroms (Å)**.

Para resolver esta frontera, la librería implementa la utilidad `to_wire_angstroms(value)` en `molsysviewer/shapes/_units.py`. Si el argumento no es un objeto de tipo cantidad de `pyunitwizard` (`puw.is_quantity` es falso), la utilidad **asume incondicionalmente que el valor numérico plano está expresado en nanómetros** y lo multiplica por 10 al enviarlo al "wire" de Mol*.

El problema de usabilidad ocurre porque en la visualización molecular clásica, los investigadores piensan y operan los radios, distancias y coordenadas en Angstroms. Si un usuario escribe:
```python
view.shapes.add_sphere(center=[10.0, 15.0, 20.0], radius=3.5)
```
esperando una esfera en coordenadas estándar de su archivo PDB (donde el radio es 3.5 Å), MolSysViewer lo interpreta como `3.5 nm` (radio de `35 Å`) y la sitúa en `[100, 150, 200] Å`. Esto genera objetos gigantescos y desplazados completamente fuera del campo visual.

---

## 2. Impacto Científico y de Experiencia de Usuario

1. **Alta Curva de Aprendizaje y Fricción**: Fuerza a los desarrolladores y científicos a envolver constantemente sus valores numéricos puros en objetos de unidades de `pyunitwizard` (ej. `puw.quantity(3.5, "angstroms")`) incluso para operaciones puramente cosméticas sobre el lienzo, lo cual resulta tedioso en celdas de exploración rápida.
2. **Errores Silenciosos de Escala**: Los usuarios nuevos del ecosistema asumen que el visor de bajo nivel se comporta como PyMOL o VMD, creando formas visuales invisibles o desproporcionadas por errores de escala de un factor de 10, lo que genera reportes de bugs inexistentes o confusión.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Alternativa A: Advertencia Científica Proactiva (`UserWarning`)
* **Descripción**: Mantener la conversión implícita de "nm por defecto" pero emitir una advertencia científica de Python (`UserWarning`) la primera vez que se reciba un número plano en APIs visuales de shapes, informando al usuario sobre la escala por defecto adoptada:
  *"Bare numeric value received. Assuming nanometers (nm) per MolSysSuite conventions. Use pyunitwizard to specify explicit units (e.g., angstroms)."*
* **Pros**: No rompe la compatibilidad hacia atrás ni la coherencia con MolSysMT, pero educa activamente al usuario en caliente.
* **Contras**: Puede resultar molesto en la salida de celdas si se repite con frecuencia.

### Alternativa B: Detección y Selección de Escala por Defecto del Visor (Recomendada)
* **Descripción**: Añadir un parámetro de configuración global en el constructor del visor, por ejemplo `length_unit_default="nm" | "angstroms"` (con valor por defecto `"nm"` para mantener consistencia con la suite). Si un usuario de visualización molecular clásica desea trabajar en coordenadas tradicionales de PDB, puede instanciar el visor con `length_unit_default="angstroms"`. La utilidad `to_wire_angstroms` consultará esta propiedad para decidir cómo interpretar los números crudos.
* **Pros**: Ofrece máxima flexibilidad y se adapta perfectamente a ambos perfiles de usuario (desarrolladores de la suite y usuarios tradicionales de visualización).
* **Contras**: Requiere acoplar la utilidad `to_wire_angstroms` al estado activo del visor (actualmente es una función de utilería pura independiente).

---

## 4. Criterios de Aceptación

1. Las llamadas a APIs visuales que reciban números crudos deben contar con un comportamiento predecible y explícitamente documentado en la API pública de `view.shapes`.
2. Si se adopta la Alternativa B, instanciar el visor con la unidad por defecto en Angstroms debe garantizar que `add_sphere(center=[1, 2, 3], radius=1)` sitúe la esfera exactamente en `[1, 2, 3] Å` de coordenadas físicas en el lienzo de Mol*, sin alteraciones de escala.
3. Se deben añadir pruebas unitarias que validen el comportamiento de la conversión de números crudos bajo ambos esquemas de configuración de unidades.
