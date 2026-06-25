# BUG: Divergencia entre estado vivo y reconstruido en `whole.set_representation` (apilado aditivo)

## Severidad

Baja-media (inconsistencia de estado tras rebuild; no rompe la sesión viva, pero el resultado
reconstruido/exportado puede no coincidir con lo que el usuario ve).

## Diagnóstico

`Whole.set_representation` (`molsysviewer/whole.py`, ~líneas 29-60) guarda en el backend de
Python **un único slot** de representación global:

```python
self._preset = normalized_preset
self._representation = normalized_repr
self._repr_params = params or {}
```

Cada llamada **sobrescribe** la anterior en Python (last-wins). Sin embargo, en el frontend
Mol* el comportamiento es **aditivo**: cada `set_global_representation` añade una representación
nueva sin eliminar las previas (decisión documentada y aceptada en
`areas_of_opportunity_analysis.md`, donde se optó por no introducir `mode="replace"`).

El problema surge en la reconstrucción. `_rebuild_view_from_current_molsys`
(`molsysviewer/viewer/core.py`, ~líneas 1031-1037) reaplica **solo la última** representación
guardada:

```python
if getattr(self.whole, "_preset", None) is not None or getattr(self.whole, "_representation", None) is not None:
    self.whole.set_representation(
        getattr(self.whole, "_representation", None),
        preset=getattr(self.whole, "_preset", None),
        skip_digestion=True,
        **getattr(self.whole, "_repr_params", {}),
    )
```

### Consecuencia observable

```python
view.whole.set_representation("cartoon")
view.whole.set_representation("ball-and-stick")   # en vivo: cartoon + ball-and-stick apilados
view.remove("water")                              # fuerza rebuild
# tras el rebuild: solo "ball-and-stick" (se pierde el cartoon apilado)
```

La escena **viva** muestra ambas representaciones apiladas; la escena **reconstruida** (y por
tanto la exportada después de un rebuild) muestra solo la última. El estado deja de ser
fielmente reproducible tras una edición estructural.

## Impacto

- Contradice parcialmente el principio rector (reproducibilidad): el rebuild "limpia" sin
  intención un estado que el usuario sí ve en vivo.
- Difícil de diagnosticar para el usuario, porque la representación cambia solo al editar la
  estructura, no al configurarla.

## Propuestas de corrección (elegir según la decisión de diseño)

### Opción A: hacer el modelo de Python coherente con el aditivo de Mol*
Si se quiere conservar el apilado aditivo, Python debe **recordar la pila completa** de
representaciones globales (lista en vez de slot único) y el rebuild debe reaplicarlas todas en
orden. Así el estado vivo y el reconstruido coinciden.

### Opción B: hacer el comportamiento vivo coherente con el modelo last-wins de Python
Introducir un `mode="replace"` (reabriendo la decisión de
`areas_of_opportunity_analysis.md`) de modo que el frontend reemplace la representación global en
cada llamada. Entonces el slot único de Python ya describe fielmente el estado, y el rebuild es
correcto por construcción. Es además el comportamiento que la mayoría de usuarios de notebook
espera entre celdas sucesivas.

### Mínimo inmediato (documentación)
Sea cual sea la decisión, documentar explícitamente en el docstring de `set_representation` que
hoy el comportamiento en vivo es **aditivo** y que tras un rebuild solo persiste la última
representación. Es un quick-win trivial que evita sorpresas mientras se decide A o B.

## Criterios de aceptación

1. El estado de representación global tras un rebuild coincide con el estado vivo previo (Opción
   A o B), o el docstring documenta de forma inequívoca la diferencia (mínimo inmediato).
2. Existe un test que aplica dos representaciones globales, fuerza un rebuild y verifica que el
   conjunto de representaciones resultante es el esperado por la opción elegida.

## Relación

- Conecta con la decisión "Modos de Coexistencia de Representaciones Globales" de
  `areas_of_opportunity_analysis.md` (allí excluida; aquí se documenta el efecto colateral
  rebuild/vivo que aquella decisión dejó abierto).
- Relacionado con [[scene_look_state_reconstruction]] (ambos son huecos del modelo de
  reconstrucción, aunque este afecta a representación estructural, no al look de escena).
