"""Real chemical systems for bounded Viewer/provider family qualification.

Peptide and protein cases use the shipped demo systems. Smaller analytical
RDKit molecules provide known positive geometries for families absent there.
No detector output is fabricated. ``make_family_view`` is shared by Python
regressions and the real Mol* browser harness.
"""

from dataclasses import dataclass

import molsysmt as msm
import numpy as np
from molsysviewer.demo import demo
from rdkit import Chem

import molsysviewer as msv


@dataclass
class FamilyFixture:
    view: object
    family: str
    function: str
    parameters: dict

    def calculate(self, name="contacts", **options):
        getter = getattr(getattr(self.view.interactions, self.family), self.function)
        return getter(name=name, **{**self.parameters, **options})


def make_family_view(kind, *, periodic=False):
    """Create a real positive family case with local, nonconsecutive frame axes.

    Small nonperiodic systems have positive frames 0 and 2 and empty frame 1.
    Periodic systems have one frame and shift the complete second fragment by
    the first vector of a triclinic box. The supplied parameters are explicit
    scientific choices, rather than changes to provider defaults.
    """
    if kind == "hbond":
        if periodic:
            raise ValueError("Use the boxed peptide qualification for H-bond PBC.")
        return FamilyFixture(
            msv.new_view(demo["pentalanine"].molsys, structure_indices=[0, 8, 3]),
            "hbonds",
            "get_buch_hbonds",
            {"distance_threshold": "0.4 nm"},
        )
    if kind == "disulfide_candidate":
        if periodic:
            raise ValueError("Use the real protein qualification for disulfide PBC.")
        return FamilyFixture(
            msv.new_view(msm.systems["2HGR"]["2hgr.pdb"]), "disulfides", "get_disulfide_candidates", {}
        )
    parameters = {}
    if kind == "ionic_contact":
        smiles = "[NH4+].CC(=O)[O-]"
        xyz = np.array([[0, 0, 0], [0.50, 0, 0], [0.36, 0, 0], [0.30, 0.08, 0], [0.30, -0.08, 0]])
        parameters = {"distance_threshold": "0.4 nm"}
        family, function = "ionic", "get_ionic_interactions"
    elif kind in {"pi_pi", "cation_pi"}:
        angles = np.arange(6) * np.pi / 3
        ring = np.column_stack((0.14 * np.cos(angles), 0.14 * np.sin(angles), np.zeros(6)))
        if kind == "pi_pi":
            smiles = "c1ccccc1.c1ccccc1"
            xyz = np.concatenate((ring, ring + [0, 0, 0.35]))
            parameters = {"profile": "three_atom_plane"}
            family, function = "pi_pi", "get_pi_pi_interactions"
        else:
            smiles, xyz = "c1ccccc1.[NH4+]", np.vstack((ring, [0, 0, 0.35]))
            family, function = "cation_pi", "get_cation_pi_interactions"
    elif kind == "halogen_bond":
        smiles = "CCl.C=O"
        xyz = np.array([[-0.15, 0, 0], [0, 0, 0], [0.36, 0.12 * np.sqrt(0.75), 0], [0.30, 0, 0]])
        family, function = "halogen_bonds", "get_halogen_bonds"
    elif kind == "hydrophobic_contact":
        smiles = "CCC.CCC"
        xyz = np.array([[0, 0, 0], [0.15, 0, 0], [0.30, 0, 0], [0, 0.30, 0], [0.15, 0.30, 0], [0.30, 0.30, 0]])
        family, function = "hydrophobic", "get_hydrophobic_interactions"
    elif kind == "metal_coordination_candidate":
        smiles, xyz = "[Zn+2].O.N", np.array([[0, 0, 0], [0.2, 0, 0], [0, 0.27, 0]])
        family, function = "metal_coordination", "get_metal_coordination"
    elif kind in {"water_bridge", "water_bridge_2"}:
        smiles = "O.N.N" if kind == "water_bridge" else "O.O.N.N"
        family, function = "water_bridges", "get_water_bridges"
        parameters = {"order": 1 if kind == "water_bridge" else 2}
    else:
        raise ValueError(f"Unknown family fixture: {kind}")
    molecule = Chem.MolFromSmiles(smiles)
    if kind.startswith("water_bridge"):
        molecule = Chem.AddHs(molecule)
        xyz = np.zeros((molecule.GetNumAtoms(), 3))
        heavy = (
            [[0, 0, 0], [-0.3, 0, 0], [0, -0.3, 0]]
            if kind == "water_bridge"
            else ([[0, 0, 0], [0.3, 0, 0], [-0.3, 0, 0], [0.6, 0, 0]])
        )
        for i, point in enumerate(heavy):
            xyz[i] = point
            hs = sorted(a.GetIdx() for a in molecule.GetAtomWithIdx(i).GetNeighbors())
            xyz[hs] = np.asarray(point) + np.array([[0, 0.1, 0], [0, -0.1, 0], [0, 0, 0.1]])[: len(hs)]
        hs = [sorted(a.GetIdx() for a in molecule.GetAtomWithIdx(i).GetNeighbors()) for i in range(len(heavy))]
        if kind == "water_bridge":
            xyz[hs[1][0]], xyz[hs[2][0]] = [-0.2, 0, 0], [0, -0.2, 0]
        else:
            xyz[hs[0][1]], xyz[hs[2][0]], xyz[hs[3][0]] = [0.1, 0, 0], [-0.2, 0, 0], [0.5, 0, 0]
    movable = list(Chem.GetMolFrags(molecule)[-1])
    if kind == "metal_coordination_candidate":
        movable = [1, 2]
    box = np.array([[2.0, 0, 0], [0.4, 2.0, 0], [0, 0.3, 2.0]])
    frames = xyz[None].copy() if periodic else np.repeat(xyz[None], 3, axis=0)
    if periodic:
        frames[0, movable] += box[0]
    else:
        frames[1, movable] += [2, 2, 2]
    system = msm.convert(molecule, to_form="molsysmt.MolSys")
    system.structures.append(
        coordinates=msm.pyunitwizard.quantity(frames, "nm"),
        box=msm.pyunitwizard.quantity(box[None], "nm") if periodic else None,
    )
    return FamilyFixture(msv.new_view(system), family, function, parameters)
