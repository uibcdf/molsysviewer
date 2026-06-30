# Propuesta pendiente: Integracion downstream de metadatos quimicos SDF/MOL2

**Estado:** pendiente, bloqueada parcialmente por MolSysMT
**Dependencia upstream:** `../molsysmt/devguide/pending_proposals/chemical_metadata_preservation_sdf_mol2.md`

## Contexto

MolSysViewer debe visualizar ligandos y moleculas pequenas sin degradar ordenes
de enlace, aromaticidad, cargas ni propiedades SDF/MOL2. La solucion general no
debe implementarse como percepcion quimica local del viewer: pertenece a
MolSysMT, porque la preservacion de esos datos es un contrato de conversion de
formas quimicas (`file:sdf`, `file:mol2`, `rdkit.Mol`, `molsysmt.MolSys`,
`molsysmt.ViewerJSON`) reutilizable por todo el ecosistema.

La propuesta upstream en MolSysMT debe definir y validar que la conversion desde
SDF/MOL2 a `molsysmt.MolSys` y `molsysmt.ViewerJSON` conserva:

- orden de enlace, incluyendo aromaticidad;
- cargas formales siguiendo el contrato de datos mecanicos de MolSysMT;
- propiedades SDF por molecula/componente;
- limites de molecula en archivos multi-ligando;
- acceso estable mediante `msm.get` o un accessor documentado.

## Estado actual en MolSysViewer

La parte TypeScript ya tiene un camino generico de carga cruda:
`load_structure_from_string` acepta `format` y llama a Mol* con
`parseTrajectory(raw, format)`. Esto permite usar el parser nativo de Mol* para
formatos como `sdf` si el frontend recibe la cadena cruda.

El camino normal de `view.load(...)`, sin embargo, es MolSysMT -> ViewerJSON ->
payload MolSysViewer. Ese camino debe esperar a que MolSysMT preserve y exponga
los metadatos quimicos necesarios. MolSysViewer no debe inferir aromaticidad,
ordenes de enlace o cargas desde coordenadas si MolSysMT ya es la fuente de la
estructura.

## Trabajo pendiente en MolSysViewer

Cuando MolSysMT exponga el contrato upstream:

1. Extender `_serialize_molsys_payload(...)` para transportar los campos
   quimicos nuevos desde `ViewerJSON` al payload TS, sin renombrados ambiguos.
2. Extender `MolSysPayload` y el loader TS para materializar ordenes de enlace,
   tipos/aromaticidad y cargas en las estructuras Mol* cuando vengan por el
   payload MolSysMT.
3. Enriquecer eventos de hover/click y add-ons con las propiedades SDF/MOL2
   transportadas por MolSysMT.
4. Anadir pruebas Python y TS que verifiquen que MolSysViewer no descarta esos
   campos al serializar, cargar y exportar/reconstruir la escena.
5. Mantener o exponer explicitamente, si se decide necesario, un camino de carga
   cruda `format="sdf"`/`format="mol2"` para casos donde el usuario quiera que
   Mol* parsee el archivo original directamente.

## Criterios de cierre local

Esta propuesta se puede cerrar en MolSysViewer cuando:

- MolSysMT tenga pruebas verdes para SDF/MOL2 -> MolSys -> ViewerJSON con
  preservacion quimica;
- MolSysViewer consuma esos campos desde ViewerJSON/payload sin perdida;
- los eventos de interaccion expongan las propiedades quimicas relevantes;
- existan pruebas de regresion que cubran al menos un SDF y un MOL2 con ordenes
  de enlace no triviales y propiedades personalizadas.
