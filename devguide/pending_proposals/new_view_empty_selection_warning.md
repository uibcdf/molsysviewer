# Propuesta de Mejora: Validación y Advertencia ante Selecciones Vacías en Cargas del Visor

## 1. Contexto y Diagnóstico

En MolSysViewer, la función de conveniencia `new_view(...)` en `molsysviewer/new_view.py` permite instanciar el visor y cargar un sistema molecular en un solo paso. Esta función admite el parámetro `load_mode="all"`, el cual:
1. Carga el sistema completo en el visor.
2. Oculta la representación global de todo el sistema (`view.whole.hide()`).
3. Crea una región llamada `"selection"` que abarca únicamente los átomos descritos en la expresión `selection` provista por el usuario, y le aplica una representación visual visible.

El problema de usabilidad radica en que **la función no valida si la expresión de selección intersecta átomos reales antes de ocultar la escena**. 

Si la expresión de `selection` suministrada por el usuario evalúa a una lista vacía (por ejemplo, debido a un error tipográfico en el nombre del ligando, como `"resname LIG"` en lugar de `"group_name == 'LIG'"`, o porque el grupo buscado no está presente en la topología):
* `msm.select` resuelve la selección como una lista vacía.
* La función procede a instanciar la región `"selection"` sin átomos y le aplica el estilo visual.
* Dado que la vista global del sistema completo fue ocultada (`view.whole.hide()`), **el usuario se encuentra con una pantalla completamente negra y vacía**, sin ninguna pista visual de la estructura molecular.

---

## 2. Impacto Científico y de Experiencia de Usuario

* **Falta de Diagnóstico y Confusión**: Los usuarios asumen que el visor ha fallado al renderizar o que existe un bug gráfico severo al ver una pantalla negra, cuando en realidad el problema es simplemente una expresión de selección que evaluó a cero átomos.
* **Fricción en Notebooks**: Dificulta la depuración interactiva rápida de consultas estructurales, obligando al usuario a escribir líneas adicionales de código con `msm.select` por separado para verificar que sus consultas son válidas antes de poder visualizarlas.

---

## 3. Propuestas de Solución (Alternativas de Diseño)

### Propuesta: Validación Temprana y Fallback de Visibilidad de Emergencia

Se propone reestructurar la lógica de inicialización en `new_view.py` para interceptar selecciones vacías antes de ocultar la escena:

1. **Validar la Intersección de la Selección**:
   Antes de ocultar la vista completa del sistema, evaluar la selección en Python:
   ```python
   resolved_atoms = view.select(selection, syntax=syntax, skip_digestion=True)
   if len(resolved_atoms) == 0:
       # Emitir una advertencia científica explícita
       import warnings
       warnings.warn(
           f"The selection query {selection!r} resolved to zero atoms. "
           "Showing the whole molecular system instead to prevent an empty screen.",
           UserWarning,
           stacklevel=2
       )
       # Cargar el sistema y mantener la representación global visible
       view.load(molecular_system, selection="all", structure_indices=structure_indices, syntax=syntax, skip_digestion=True)
       return view
   ```

2. **Beneficios de Diseño**:
   * Previene la visualización de la pantalla negra frustrante de forma incondicional.
   * Proporciona feedback claro e instructivo en tiempo de ejecución sobre por qué la consulta del usuario falló.
   * Mantiene el sistema visible por defecto para que el usuario pueda inspeccionar la topología real y corregir su consulta.

---

## 4. Criterios de Aceptación

1. Llamar a `new_view` con `load_mode="all"` y una expresión de selección que resuelva a cero átomos no debe producir una pantalla de visualización completamente negra y vacía de forma silenciosa.
2. Ante una selección vacía, el visor debe emitir una advertencia descriptiva (`UserWarning`) en Python, mantener la visibilidad global del sistema molecular activa y omitir la creación de la región vacía.
3. Se deben incorporar pruebas unitarias que evalúen el comportamiento de `new_view` alimentándolo con selecciones inválidas o vacías, verificando que se lanza la advertencia y se conserva la visibilidad del sistema completo.
