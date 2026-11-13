"""Explicit prepared-demo controls for the integrated Movie workflow.

This is a rendering/integration fixture, not a binding prediction. MolSysMT's
prepared lysozyme/HED example supplies the chemistry and coordinates. A relaxed
0.40 nm H--A cutoff intentionally supplies a candidate at 0.35 nm; the default
0.23 nm criterion yields no ligand/protein candidates. Neither is hidden.
Structures 1 and 2 are labeled synthetic controls, not a simulated trajectory.
"""

import hashlib
from pathlib import Path

import molsysmt as msm
from molsysviewer._pyunitwizard import puw

import molsysviewer as msv

ANALYSIS = "story-buch-candidates"
DEFAULT_ANALYSIS = "story-buch-default"
TIMES = [0, 500, 1000, 1500, 2000, 2500]


def make_story_view():
    source = msm.systems["T4 lysozyme L99A"]["t4_lysozyme_L99A.h5msm"]
    prepared = msm.convert(source)
    selection = "molecule_type=='protein' or group_name=='HED'"
    source_atoms = msm.select(prepared, selection=selection)
    molsys = msm.extract(prepared, selection=selection, structure_indices=[0, 0, 0])
    ligand = list(msm.select(molsys, selection="group_name=='HED'"))
    protein = list(msm.select(molsys, selection="molecule_type=='protein'"))
    pocket = list(msm.select(molsys, selection="molecule_type=='protein' and group_id in ['68','72','93']"))
    assert ligand and protein and pocket
    # Explicit test input: move only HED by 10 nm before calculating anything.
    moved = msm.get(molsys, selection=ligand, structure_indices=[1], coordinates=True)
    msm.set(
        molsys,
        selection=ligand,
        structure_indices=[1],
        coordinates=puw.quantity(puw.get_value(moved, to_unit="nm") + [10, 0, 0], "nm"),
    )
    view = msv.new_view(molsys)
    try:
        default = view.interactions.hbonds.get_buch_hbonds(
            name=DEFAULT_ANALYSIS,
            selection=ligand,
            selection_2=protein,
            structure_indices=[0, 1],
            pbc=False,
        )
        assert default.n_interactions == 0
        result = view.interactions.hbonds.get_buch_hbonds(
            name=ANALYSIS,
            selection=ligand,
            selection_2=protein,
            structure_indices=[0, 1],
            distance_threshold="0.40 nm",
            pbc=False,
        )
        assert result.n_interactions > 0
        assert result.evaluated_structure_indices.tolist() == [0, 1]
        relation = result.relation(int(result.query(structure_indices=[0]).to_dict()["relation_indices"][0]))
        roles = {row["role"]: row["atom_indices"].tolist() for row in relation["participants"]}
        hydrogen, acceptor = roles["hydrogen"][0], roles["acceptor"][0]
        coordinates = puw.get_value(view.get_coordinates(), to_unit="angstrom")
        site = coordinates[0, ligand].mean(axis=0)
        distances = (
            puw.get_value(
                msm.structure.get_distances(
                    molsys,
                    selection=[hydrogen],
                    selection_2=[acceptor],
                    pbc=False,
                ),
                to_unit="nm",
            )
            .reshape(-1)
            .tolist()
        )
        assert 0.23 < distances[0] <= 0.40 and distances[1] > 5
        context = {
            "schema": "molsysviewer.movie_story_control@1",
            "source": {
                "system": "T4 lysozyme L99A",
                "file": Path(source).name,
                "sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                "preparation": "supplied MolSysMT prepared example; no preparation run by Movie",
            },
            "source_atom_indices": [int(i) for i in source_atoms],
            "source_structure_indices": [0, 0, 0],
            "controls": ["supplied pose", "synthetic HED translation +10 nm along x", "supplied copy; not evaluated"],
            "calculation": {
                "method": result.method,
                "distance_threshold_nm": 0.4,
                "pbc": False,
                "interpretation": "relaxed geometric candidates; not a binding or hydrogen-bond-strength claim",
                "default_0_23_nm_ligand_protein_result": "empty",
            },
            "units": {"distance": "nm", "coordinates": "angstrom", "movie_time": "ms"},
            "ligand": ligand,
            "pocket": pocket,
            "hydrogen": hydrogen,
            "acceptor": acceptor,
            "distances_nm": distances,
        }
        view.whole.hide()
        view.regions.add(atom_indices=protein, tag="protein", representation="cartoon", color=0x537DA8)
        view.regions.add(atom_indices=pocket, tag="pocket", representation="ball-and-stick", color=0x36B7D4).hide()
        view.regions.add(atom_indices=ligand, tag="ligand", representation="ball-and-stick", color=0xF28E2B).hide()
        view.interactions.add(ANALYSIS, tag="contacts").hide()
        view.interactions["contacts"].set_color(0xD32F9D)
        view.interactions["contacts"].set_radius("0.035 nm")
        view.annotations.add("HED ligand", atom_indices=[ligand[0]], tag="ligand-label").hide()
        view.annotations.add(
            "181L prepared example",
            position=puw.quantity(site, "angstrom"),
            offset_mode="camera",
            offset=(0, 4, 18),
            tag="phase",
        )
        view.measurements.add_distance([hydrogen], [acceptor], tag="candidate-distance").hide()
        view.trajectory_plot.show(
            {"H-A distance": distances},
            tag="candidate-distance",
            x_label="Control structure index",
            y_label="H-A distance (nm)",
            title="Coordinate distance; coverage is separate",
            colors=[0x149A49],
            width=380,
            height=220,
            observations=[context],
        )
        view.scene.set_legend([("HED ligand", 0xF28E2B), ("Buch candidates: H-A <= 0.40 nm", 0xD32F9D)])
        view.scene.set_background(0xFFFFFF)
        view.scene.set_lighting(ambient=0.6, diffuse=0.6)
        centre = coordinates[0, protein].mean(axis=0)
        overview = {"position": (centre + [0, 0, 105]).tolist(), "target": centre.tolist(), "up": [0, 1, 0]}
        close = {"position": (site + [0, 0, 32]).tolist(), "target": site.tolist(), "up": [0, 1, 0]}
        final = {"position": (centre + [80, 20, 70]).tolist(), "target": centre.tolist(), "up": [0, 1, 0]}
        view.movie.set_baseline(3000, camera=overview)

        def track(tag, domain, prop, keys, target=None):
            view.movie.add_track(
                {
                    "tag": tag,
                    "target": {"domain": domain, **({"tag": target} if target else {})},
                    "property": prop,
                    "keys": [{"time_ms": at, "value": value} for at, value in keys],
                }
            )

        track("camera", "camera", "pose", [(500, close), (1000, close), (2500, final), (3000, final)])
        track("structures", "structure", "index", [(1500, 1), (2000, 2), (2500, 0)])
        track("pocket", "region", "visible", [(500, True)], "pocket")
        track("ligand", "region", "visible", [(1000, True)], "ligand")
        track("contacts", "interaction", "visible", [(1000, True)], "contacts")
        track("ligand-label", "annotation", "visible", [(1000, True)], "ligand-label")
        track("distance", "measurement", "visible", [(1000, True), (1500, False), (2500, True)], "candidate-distance")
        track("ligand-style", "region", "representation", [(1000, "ball-and-stick"), (2500, "spacefill")], "ligand")
        track("lighting", "scene", "lighting", [(1000, {"ambient": 0.7, "diffuse": 0.6})])
        track(
            "phase",
            "annotation",
            "text",
            [
                (1000, "Buch candidates: H-A <= 0.40 nm"),
                (1500, "Synthetic separation: evaluated empty"),
                (2000, "Supplied copy: not evaluated"),
                (2500, "Supplied pose restored"),
            ],
            "phase",
        )
        return view, context
    except BaseException:
        view.close()
        raise
