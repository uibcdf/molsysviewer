# Propuesta pendiente: integracion downstream de metadatos quimicos SDF/MOL2

**Estado:** pendiente, bloqueada por MolSysMT
**Dependencia upstream:** `../molsysmt/devguide/pending_proposals/chemical_metadata_preservation_sdf_mol2.md`

## Estado actual en MolSysViewer

MolSysViewer no debe implementar percepcion quimica local para SDF/MOL2. La preservacion de ordenes de enlace, aromaticidad, cargas y propiedades SDF/MOL2 pertenece a MolSysMT, porque es un contrato de conversion entre formas quimicas reutilizable por todo el ecosistema.

La parte local que ya existe en MolSysViewer:

- `formal_charge` ya se consume desde `ViewerJSON.atoms`, se serializa en el payload MolSysViewer y se materializa en TypeScript como `atom_site.pdbx_formal_charge`.
- `bonds.indexA`, `bonds.indexB` y `bonds.order` ya forman parte del payload TS cuando MolSysMT los entrega.
- `residue_id` / `residue_name` son intencionales en el payload Python -> TS: el loader TypeScript los materializa como columnas Mol*/mmCIF `atom_site` (`label_seq_id`, `auth_seq_id`, `label_comp_id`, `auth_comp_id`). Las APIs Python y los eventos de interaccion siguen exponiendo vocabulario `group_*` donde corresponde.
- El camino crudo frontend `load_structure_from_string(raw, format)` sigue permitiendo usar el parser nativo de Mol* para formatos soportados cuando el usuario decide evitar el camino MolSysMT -> ViewerJSON.

## Problema que sigue pendiente

El camino normal `view.load(...)` usa MolSysMT -> ViewerJSON -> payload MolSysViewer. Ese camino todavia depende de que MolSysMT preserve y exponga, en su `ViewerJSON`, los metadatos quimicos relevantes de SDF/MOL2.

Mientras MolSysMT no cierre ese contrato, MolSysViewer no puede cerrar esta propuesta sin inventar una solucion local duplicada y menos general.

## Trabajo pendiente en MolSysViewer cuando MolSysMT exponga el contrato

1. Consumir los campos nuevos de `ViewerJSON` sin renombrados ambiguos.
2. Extender `MolSysPayload` y el loader TS solo para los campos que MolSysMT haga contractuales, por ejemplo:
   - aromaticidad o tipo de enlace estable;
   - `partial_charge`;
   - metadatos SDF por molecula/componente;
   - identificadores estables de enlace si se exponen.
3. Enriquecer hover/click/context-menu y add-ons con las propiedades quimicas transportadas por MolSysMT.
4. Anadir regresiones Python y TS que verifiquen que MolSysViewer no descarta esos campos al serializar, cargar, exportar y reconstruir.
5. Mantener el camino crudo `format="sdf"`/`format="mol2"` como una opcion explicita, no como sustituto del contrato MolSysMT.

## Criterios de cierre local

Esta propuesta se puede cerrar en MolSysViewer cuando:

- MolSysMT tenga pruebas verdes para SDF/MOL2 -> MolSys -> ViewerJSON con preservacion de orden de enlace, aromaticidad/tipo, cargas y propiedades SDF/MOL2;
- MolSysViewer consuma esos campos desde ViewerJSON/payload sin perdida;
- los eventos de interaccion expongan las propiedades quimicas relevantes;
- existan pruebas de regresion locales con al menos un SDF y un MOL2 con ordenes de enlace no triviales y propiedades personalizadas.
