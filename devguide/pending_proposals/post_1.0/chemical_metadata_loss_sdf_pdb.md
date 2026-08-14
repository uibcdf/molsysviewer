---
summary: Preserve enriched chemical metadata from SDF and MOL2.
issue: uibcdf/molsysviewer#46
status: open
opened: 2026-07-03
closed:
verification: inspected
area: [molsysmt, forms]
guard:
normative:
blocked_by: []
supersedes: []
---

# Propuesta post-1.0: metadatos quimicos SDF/MOL2 enriquecidos

**Estado:** post-1.0
**Dependencia upstream:** `../molsysmt/devguide/pending_proposals/chemical_metadata_preservation_sdf_mol2.md`

## Contexto

La parte minima necesaria antes de 1.0 queda acotada al contrato basico
`molsysmt.MolSys` -> proyeccion MolSysViewer:

- `formal_charge` via `MolecularMechanics` en MolSysMT y
  `atoms.formal_charge` en la proyeccion;
- `bonds.order` para ordenes numericos cuando sean compatibles con Mol*;
- `bonds.type` para conservar etiquetas como `single`, `double` o `aromatic` sin hacer percepcion quimica local.

MolSysViewer no debe implementar percepcion quimica local para SDF/MOL2. La preservacion general de ordenes de enlace, aromaticidad, cargas y propiedades SDF/MOL2 pertenece a MolSysMT porque es un contrato reutilizable por todo el ecosistema.

## Estado local pre-1.0

La parte local pre-1.0 es deliberadamente pequena:

- `formal_charge` se lee directamente del `MolSys`, se serializa en el payload
  MolSysViewer y se materializa en TypeScript como
  `atom_site.pdbx_formal_charge`.
- `bonds.indexA`, `bonds.indexB`, `bonds.order` y `bonds.type` se mantienen en el payload cuando MolSysMT los entrega. Mol* usa el orden numerico para la topologia; `type` queda transportado como metadata disponible para consumo posterior.
- `residue_id` / `residue_name` son intencionales en el payload Python -> TS: el loader TypeScript los materializa como columnas Mol*/mmCIF `atom_site` (`label_seq_id`, `auth_seq_id`, `label_comp_id`, `auth_comp_id`). Las APIs Python y los eventos de interaccion siguen exponiendo vocabulario `group_*` donde corresponde.
- El camino crudo frontend `load_structure_from_string(raw, format)` sigue
  permitiendo usar el parser nativo de Mol* para formatos soportados cuando el
  usuario decide evitar la conversion a `molsysmt.MolSys` y la proyeccion de
  MolSysViewer.

## Trabajo diferido para despues de 1.0

1. Consumir el contrato post-1.0 de MolSysMT para propiedades SDF/MOL2 por molecula, componente, atomo o enlace.
2. Enriquecer hover/click/context-menu con propiedades quimicas como aromaticidad, partial charges, docking scores, supplier IDs o campos custom SDF.
3. Definir UI para inspeccionar metadatos de SDF multi-molecula sin saturar eventos ni payloads.
4. Anadir estilos visuales opcionales por tipo quimico cuando MolSysMT exponga un contrato estable.
5. Mantener el camino crudo `format="sdf"`/`format="mol2"` como una opcion explicita, no como sustituto del contrato MolSysMT.

## Criterios de cierre post-1.0

Esta propuesta se puede cerrar despues de 1.0 cuando:

- MolSysMT tenga un contrato estable para propiedades SDF/MOL2 enriquecidas y multi-molecula;
- MolSysViewer consuma esos campos directamente desde `MolSys` y los proyecte
  sin perdida;
- los eventos de interaccion expongan las propiedades quimicas relevantes;
- existan pruebas de regresion locales con al menos un SDF y un MOL2 con ordenes de enlace no triviales y propiedades personalizadas.
