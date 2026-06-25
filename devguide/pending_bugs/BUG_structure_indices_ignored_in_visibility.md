# BUG: `structure_indices` aceptado pero ignorado en los métodos de visibilidad

## Severidad

Media-alta (defecto de diseño visible para el usuario: la API promete una capacidad que no
existe y falla en silencio).

## Diagnóstico

En `molsysviewer/viewer/visibility.py`, los cuatro métodos públicos de visibilidad declaran el
parámetro `structure_indices` en su firma:

- `hide(selection="all", structure_indices="all", syntax=..., ...)` (línea ~16)
- `show(selection="all", structure_indices="all", syntax=..., ...)` (línea ~35)
- `isolate(selection="all", structure_indices="all", syntax=..., ...)` (línea ~63)
- `focus_with_fade(selection="all", *, ..., structure_indices="all", ...)` (línea ~81)

Sin embargo, **ninguno usa `structure_indices` para acotar el efecto por estructura/frame**. La
visibilidad se modela con un único `self.atom_mask` unidimensional (un booleano por átomo, sin
dimensión de estructura). En `show()` el valor de `structure_indices` solo se consulta como
parte de la condición `is_all(selection) and is_all(structure_indices)` para decidir entre
"reset total" y "parcial", pero **nunca restringe a qué estructuras se aplica el cambio**.

### Consecuencia observable

```python
view.hide("water", structure_indices=[5])
```

El usuario espera ocultar el agua **solo en el frame 5**. En realidad el agua se oculta en
**todas** las estructuras de la trayectoria, sin ningún aviso. La API insinúa control de
visibilidad por estructura que el backend no implementa.

## Impacto

- **Confusión y pérdida de confianza**: el usuario no entiende por qué su argumento no tiene
  efecto; puede asumir que la librería está rota o malinterpretar resultados científicos
  (p. ej. creer que una conformación tiene el agua oculta cuando en realidad lo está en todas).
- Es el tipo de fallo más dañino para la curva de aprendizaje: un parámetro presente y
  silenciosamente inerte.

## Propuestas de corrección (elegir una)

### Opción A (recomendada a corto plazo): rechazar explícitamente
Si la visibilidad por estructura no está en el alcance de esta versión, **no aceptar el
argumento en silencio**. Lanzar `NotImplementedError` (o emitir un warning vía `smonitor`)
cuando `structure_indices` no sea `"all"`, de modo que el contrato sea honesto:

```python
if not is_all(structure_indices):
    raise NotImplementedError(
        "Per-structure visibility is not supported yet; structure_indices must be 'all'."
    )
```

### Opción B (alcance mayor): implementar visibilidad por estructura
Promover `atom_mask` a una máscara 2D (estructuras × átomos) o introducir una
`structure_mask`/máscara compuesta, y propagar la dimensión de estructura hasta la op
`update_visibility` y su handler TS. Esto encaja con la futura visibilidad por frame, pero es
un cambio de modelo de estado con implicaciones en rebuild/export y debería diseñarse como
propuesta aparte si se decide acometerlo.

## Criterios de aceptación

1. Llamar a cualquier método de visibilidad con `structure_indices` distinto de `"all"` produce
   un efecto coherente con la documentación: o bien acota realmente por estructura (Opción B),
   o bien falla/avisa de forma explícita (Opción A). En ningún caso se ignora en silencio.
2. Existe un test que verifica el comportamiento elegido con una vista demo multi-estructura.

## Relación

- Comparte raíz con la filosofía de [[silent_exception_desync]] (estado que cambia sin aviso).
