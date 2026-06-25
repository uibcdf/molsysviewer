# Propuesta de Mejora: Vectorizar la Serialización de Columnas del Payload de Carga (`_column`)

## 1. Contexto y Diagnóstico

`_serialize_molsys_payload` en `molsysviewer/loaders/load_molsysmt.py` construye el payload de
átomos que viaja al frontend. Para cada columna de metadatos atómicos llama al helper `_column`
(~líneas 146-164), y lo hace **13 veces** por carga: `atom_id`, `atom_name`, `residue_id`,
`residue_name`, `chain_id`, `entity_id`, `element_symbol`, `formal_charge`, `molecule_id`,
`molecule_name`, `component_id`, `component_name`, `group_type` (~líneas 166-180).

`_column` ejecuta, **por columna**, un bucle Python puro átomo a átomo con `try/except` y un
`cast(v)` por elemento:

```python
def _column(values, fallback, cast):
    ...
    out: list[Any] = []
    for i, v in enumerate(array.tolist()):
        try:
            val = cast(v)
            if isinstance(val, float) and not math.isfinite(val):
                val = fallback(i)
        except Exception:
            val = fallback(i)
        out.append(val)
    return out
```

Para un sistema de decenas o cientos de miles de átomos, esto son **13 bucles interpretados de
longitud `n_atoms`** con manejo de excepciones por elemento, en plena ruta caliente de carga
(la carga es ya de por sí pesada por las coordenadas; estos bucles se suman al coste).

## 2. Impacto

- Tiempo de carga perceptiblemente mayor en sistemas grandes (proteínas grandes, sistemas
  solvatados), justo donde el usuario más nota la latencia.
- El coste es proporcional a `13 × n_atoms` en Python puro, evitable en el caso común.

## 3. Análisis

En la inmensa mayoría de las cargas, los arrays que llegan de MolSysMT ya tienen la forma
correcta (`shape[0] == n_atoms`) y valores válidos; el camino elemento-a-elemento con `try/except`
solo es necesario para el **fallback** (datos ausentes, NaN/inf, longitud incorrecta). Conviene
separar el camino rápido del lento:

- **Camino rápido (vectorizado)**: si `np.asarray(values)` tiene la forma esperada, castear de
  golpe con `array.astype(dtype).tolist()` y, para columnas float, comprobar finitud con una
  única operación vectorial `np.isfinite(array)`; solo si hay no-finitos se aplica el reemplazo
  por fallback en las posiciones afectadas (máscara), no por bucle global.
- **Camino lento (actual)**: reservarlo solo para cuando el array no tiene la forma esperada o
  no es convertible.

## 4. Propuesta de Solución

Reescribir `_column` con dispatch por tipo de fallback (entero/string/float) y fast-path
vectorizado:

```python
def _column(values, fallback, cast, *, dtype=None):
    array = _as_array_or_none(values, n_atoms)
    if array is None:
        return [fallback(i) for i in range(n_atoms)]
    # fast-path: cast vectorizado
    try:
        if dtype is not None:
            out = array.astype(dtype)
            if np.issubdtype(out.dtype, np.floating):
                bad = ~np.isfinite(out)
                if bad.any():
                    idx = np.nonzero(bad)[0]
                    out = out.tolist()
                    for i in idx:
                        out[i] = fallback(int(i))
                    return out
            return out.tolist()
    except Exception:
        pass
    # slow-path: elemento a elemento (comportamiento actual)
    ...
```

(Ajustar a las firmas reales; pasar el `dtype` esperado por columna desde el sitio de llamada,
que ya conoce si la columna es int/str/float.)

## 5. Criterios de Aceptación

1. El payload generado para una vista demo es **idéntico** (mismos valores y fallbacks) al
   generado por la implementación actual — cubierto por un test de igualdad de payload sobre
   `dialanine`/`pentalanine`/`tctim` y un caso con datos ausentes/no finitos para ejercitar el
   fallback.
2. Una medición de carga sobre un sistema grande (p. ej. `chicken_villin_HP35` o un sistema
   solvatado del benchmark) muestra reducción del tiempo gastado en `_serialize_molsys_payload`.
3. El camino lento sigue cubriendo los casos de forma incorrecta / datos corruptos sin regresión.

## 6. Relación

- Complementaria a [[zero_copy_visual_rendering]] / [[visual_scaling_zero_copy]] /
  [[jupyter_websocket_redundancy_overflow]]: aquellas atacan el transporte de **coordenadas**
  (el coste dominante); esta ataca el coste de **metadatos atómicos** en Python, que es
  independiente y de implementación mucho más barata.
