# BUG: Op huérfana `update_coordinates` en el benchmark de serialización

## Severidad

Baja (no afecta a la API pública ni al runtime real; afecta a la validez de un benchmark interno).

## Diagnóstico

El benchmark `benchmark_serialization()` en `molsysviewer/tools/benchmark.py` (~línea 114)
mide la latencia de `json.dumps` sobre un payload "de alta frecuencia" cuyo `op` es
`update_coordinates`:

```python
coords_payload = {
    "op": "update_coordinates",
    "coordinates": coords_list,
    "structure_indices": 0,
}
```

`update_coordinates` es la **única op enviada desde Python que el frontend TypeScript no
maneja**. El `switch (msg.op)` de `js/src/managers/viewer-controller.ts` no tiene un `case`
para ella. La ruta real de actualización de coordenadas en caliente es
`partial_coordinates_update` (implementada en Python y TS), que es la que de hecho mutaría
los buffers WebGL.

Por tanto, el benchmark está midiendo la serialización de un mensaje que:

1. ya no corresponde a ninguna op viva del protocolo, y
2. tiene una forma de payload distinta a la op real que sí existe
   (`partial_coordinates_update` usa `coords_ang`/`atom_indices`/`transaction_id`,
   no `coordinates`/`structure_indices`).

El resultado del benchmark no es incorrecto numéricamente (mide `json.dumps` de *un* dict),
pero **no representa el coste de serialización de la op real**, que es lo que pretende medir.

## Cómo confirmarlo

- `grep -rn "update_coordinates"` en `molsysviewer/` (excluyendo `viewer.js`) solo aparece en
  `tools/benchmark.py`.
- No existe `case "update_coordinates"` en `viewer-controller.ts`.
- La op viva equivalente es `partial_coordinates_update` (ver checkpoint "twenty-second batch").

## Propuesta de corrección

Actualizar el payload del benchmark para reflejar la op real y su forma actual:

```python
coords_payload = {
    "op": "partial_coordinates_update",
    "coords_ang": coords_list,
    "atom_indices": list(range(500)),
    "transaction_id": 1,
}
```

(verificar los nombres exactos de campo contra la implementación de
`partial_coordinates_update` en Python/TS antes de fijarlos).

Alternativamente, si se quiere conservar un payload genérico de "coordenadas crudas" solo
como referencia de tamaño, renombrar la clave `op` a algo que deje claro que es sintético
(p. ej. `"_benchmark_raw_coordinates"`) para que no aparezca en los barridos de consistencia
de protocolo como una op real huérfana.

## Criterios de aceptación

1. Ninguna op presente en código Python fuera de los tests carece de `case` en el `switch` de
   `viewer-controller.ts` (salvo que esté marcada explícitamente como sintética).
2. El benchmark de serialización mide el payload de la op de coordenadas que el runtime usa de
   verdad.
