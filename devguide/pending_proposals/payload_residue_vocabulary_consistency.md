# Propuesta de Verificación: Consistencia de Vocabulario `residue` vs `group` en el Payload de Carga

## 1. Contexto y Diagnóstico

> Nota: esto se reporta como **verificación/documentación**, no como bug confirmado. El
> comportamiento descrito es probablemente **intencional**; el objetivo es confirmarlo y dejarlo
> documentado, o corregirlo si resultara una fuga de vocabulario.

El ecosistema MolSysSuite usa el vocabulario `group` (`group_id`, `group_name`, `group_index`),
y la normalización de eventos de interacción del frontend (ver
`areas_of_opportunity_analysis.md`) insiste explícitamente en evitar el término heredado
`residue`.

Sin embargo, `_serialize_molsys_payload` en `molsysviewer/loaders/load_molsysmt.py` **remapea**
las columnas `group_id`/`group_name` del ViewerJSON de MolSysMT a claves `residue_id` /
`residue_name` en el payload que viaja al frontend (~líneas 168-169 y 193-194):

```python
residue_id   = _column(atoms_block.get("group_id"),   lambda _i: 1,     int)
residue_name = _column(atoms_block.get("group_name"), lambda _i: "RES", str)
...
"residue_id":   residue_id,
"residue_name": residue_name,
```

Esto crea una asimetría: el **payload estructural** habla de `residue_*`, mientras que los
**eventos de interacción enriquecidos** y la API pública hablan de `group_*`.

## 2. Hipótesis (por confirmar)

Lo más probable es que el uso de `residue_*` en el payload sea **deliberado y correcto**, porque
el constructor de modelos de Mol* está alineado con el modelo mmCIF, que usa la nomenclatura
`residue` / `auth_seq_id`. Es decir, `residue_*` sería el vocabulario del **límite con Mol***, no
una fuga del vocabulario heredado hacia la superficie de MolSysSuite. (Conviene notar también
que la regla #7 de `AGENTS.md` prohíbe explícitamente `positions`/`frames`, pero **no** menciona
`residue`.)

## 3. Acción Propuesta

1. **Confirmar la intención**: verificar en el handler TS (`loader-handlers.ts` /
   `plugin/structure.ts`) que las claves `residue_id`/`residue_name` se consumen porque el
   builder mmCIF de Mol* las espera con ese nombre.
2. Si es intencional (lo esperado): **documentarlo** con un comentario en
   `_serialize_molsys_payload` explicando que `residue_*` es el vocabulario del límite Mol*/mmCIF
   y que el remapeo `group_* → residue_*` es deliberado, para que ningún futuro contribuyente lo
   "corrija" por error ni lo confunda con una fuga de vocabulario.
3. Si **no** fuera intencional: renombrar a `group_*` en el payload y ajustar el consumidor TS,
   alineando ambos caminos (estructural e interacción) con el vocabulario MolSysSuite.

## 4. Criterios de Aceptación

1. Queda registrado (en código y/o devguide) por qué el payload usa `residue_*` mientras el
   resto de la superficie usa `group_*`, o ambos caminos quedan alineados.
2. No queda ambigüedad para futuros contribuyentes sobre cuál es el vocabulario correcto en cada
   límite (MolSysSuite/API ↔ payload/Mol*).

## 5. Relación

- Contexto de vocabulario de interacción en `areas_of_opportunity_analysis.md` (payloads
  enriquecidos con `group_name`/`group_id`, evitando `residue`).
