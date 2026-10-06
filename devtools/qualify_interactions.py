"""Qualify real detector results at the Viewer boundary; no mocked provider.

Run with the scientific backend to qualify at the front of sys.path. A source
checkout is useful evidence but cannot certify a published dependency release.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") != "1":
    sys.path.insert(0, str(ROOT))

import molsysmt as msm  # noqa: E402
import numpy as np  # noqa: E402
from molsysviewer.interactions import _analysis_signature, _to_plain  # noqa: E402

import molsysviewer as msv  # noqa: E402

ANGSTROM_POLICY = ["angstrom", "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]
SOURCE_FRAMES = [4999, 0, 73, 3]
EVALUATED_FRAMES = [3, 0, 2]


def peak_rss_mib():
    """Keep scientific checks portable; this memory observation is Linux-only."""
    if sys.platform != "linux":
        return None
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def trajectory_view():
    return msv.new_view(msm.systems["pentalanine"]["traj_pentalanine.h5msm"], structure_indices=SOURCE_FRAMES)


def observed_geometry(view, name, tag, frames=None):
    """Independently reconstruct positions from scientific columns and quantities."""
    result = view.interactions.get_analysis(name)
    data = result.to_dict()
    xyz = np.asarray(msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm"))
    raw_box = msm.get(view.molsys, box=True)
    boxes = None if raw_box is None else np.asarray(msm.pyunitwizard.get_value(raw_box, to_unit="nm"))
    expected = {}
    participants_by_occurrence = {}
    nonzero_images = 0
    assert data["occurrence_indices"].dtype == np.dtype("int64")
    assert data["measure_units"]["distance"] == "nm"
    for row, occurrence in enumerate(data["occurrence_indices"]):
        relation = result.relation(int(data["relation_indices"][row]))
        parts = relation["participants"]
        frame = int(data["structure_indices"][row])
        atoms = [int(p["atom_indices"][0]) for p in parts]
        positions = xyz[frame, atoms].copy()
        if data["image_vectors"] is not None:
            lo, hi = data["image_offsets"][row : row + 2]
            images = data["image_vectors"][lo:hi]
            assert boxes is not None
            positions += (images - images[0]) @ boxes[frame]
            nonzero_images += int(np.any(images - images[0]))
        if relation["interaction_type"] == "hbond":
            roles = {p["role"]: i for i, p in enumerate(parts)}
            start, end = positions[[roles["hydrogen"], roles["acceptor"]]]
        else:
            assert relation["interaction_type"] == "disulfide_candidate"
            start, end = positions
        distance = float(np.linalg.norm(end - start))
        np.testing.assert_allclose(distance, data["measurements"]["distance"][row], rtol=1e-7, atol=1e-8)
        expected[int(occurrence)] = (frame, start, end)
        participants_by_occurrence[int(occurrence)] = set(atoms)
    assert expected, "This positive detector workload produced no observations."
    for frame in range(result.n_structures) if frames is None else frames:
        message = next(m for m in view.interactions._messages(frame) if m["tag"] == tag)
        assert message["coordinate_unit"] == "nm"
        wanted = {i for i, (f, _, _) in expected.items() if f == frame}
        assert message["status"] == ("evaluated" if frame in result.evaluated_structure_indices else "unevaluated")
        assert message["n_supported"] == len(wanted) and message["n_skipped"] == 0
        assert {link["occurrence_index"] for link in message["links"]} == wanted
        for link in message["links"]:
            _, start, end = expected[link["occurrence_index"]]
            np.testing.assert_allclose(link["start"], start, atol=1e-8)
            np.testing.assert_allclose(link["end"], end, atol=1e-8)
    return expected, participants_by_occurrence, nonzero_images


def query_checks(view, name, participants):
    first = next(iter(participants.values()))
    atoms = {min(first), max(first)}
    frames = [2, 0] if view.molsys.structures.n_structures > 2 else [0]
    data = view.interactions.get_analysis(name).to_dict()
    frame_by_occurrence = dict(zip(data["occurrence_indices"].tolist(), data["structure_indices"].tolist()))
    for mode in ("involving_selection", "within_selection", "across_selection_boundary"):
        expected = {
            i
            for i, part in participants.items()
            if frame_by_occurrence[i] in frames
            and (
                bool(part & atoms)
                if mode == "involving_selection"
                else part <= atoms
                if mode == "within_selection"
                else bool(part & atoms) and bool(part - atoms)
            )
        }
        actual = view.interactions.query(name, selection=sorted(atoms), structure_indices=frames, mode=mode).to_dict()
        assert set(actual["occurrence_indices"].tolist()) == expected
    a, b = {min(first)}, {max(first)}
    expected = {i for i, part in participants.items() if frame_by_occurrence[i] in frames and part & a and part & b}
    actual = view.interactions.query(
        name, selection=sorted(a), selection_2=sorted(b), structure_indices=frames, mode="between_selections"
    ).to_dict()
    assert set(actual["occurrence_indices"].tolist()) == expected


def round_trips(view, directory, name="buch", tag="real-hb"):
    directory.mkdir(parents=True, exist_ok=True)
    signatures = {
        item["name"]: _analysis_signature(view.interactions.get_analysis(item["name"]))
        for item in view.interactions.analyses()
    }
    full, standalone, session = (
        directory / filename for filename in ("complete.h5msm", "interactions.h5msm", "scene.msv")
    )
    msm.h5msm.write(view.molsys, str(full))
    msm.h5msm.write_layers(str(standalone), interactions=dict(view.molsys.interactions))
    expected_xyz = msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm")
    for source in (full, standalone):
        target_system = view.molsys.copy()
        target_system.interactions = {}
        target = msv.new_view(target_system)
        try:
            for analysis in signatures:
                result = target.interactions.load(source, analysis_name=analysis, assume_aligned=True)
                assert _analysis_signature(result) == signatures[analysis]
            np.testing.assert_array_equal(
                msm.pyunitwizard.get_value(msm.get(target.molsys, coordinates=True), to_unit="nm"), expected_xyz
            )
        finally:
            target.close()
    view.save_session(session)
    restored = msv.load_session(session)
    try:
        assert restored.export_state() == view.export_state()
        assert {a["name"] for a in restored.interactions.analyses()} == set(signatures)
        for analysis, signature in signatures.items():
            assert _analysis_signature(restored.interactions.get_analysis(analysis)) == signature
        observed_geometry(restored, name, tag)
        return restored._build_embedded_runtime_snapshot()
    finally:
        restored.close()


def qualify_trajectory(directory):
    started = time.perf_counter()
    view = trajectory_view()
    try:
        result = view.interactions.hbonds.get_buch_hbonds(
            name="buch", structure_indices=EVALUATED_FRAMES, distance_threshold="4 angstroms"
        )
        np.testing.assert_array_equal(result.evaluated_structure_indices, EVALUATED_FRAMES)
        assert result.n_structures == 4 and result.n_atoms == 62
        view.interactions.add("buch", tag="real-hb")
        expected, participants, _ = observed_geometry(view, "buch", "real-hb")
        query_checks(view, "buch", participants)
        empty = view.interactions.hbonds.get_buch_hbonds(
            name="empty", structure_indices=[1], distance_threshold="0.01 nm"
        )
        assert empty.n_interactions == 0
        np.testing.assert_array_equal(empty.evaluated_structure_indices, [1])
        view.interactions.disulfides.get_disulfide_candidates(name="no-cysteines", structure_indices=[3, 0])
        restored = round_trips(view, directory)
        return {
            "case": "trajectory",
            "atoms": result.n_atoms,
            "source_frames": SOURCE_FRAMES,
            "evaluated_local_frames": EVALUATED_FRAMES,
            "observations": len(expected),
            "round_trips": ["complete H5MSM", "interactions-only H5MSM", "MSV session"],
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "restored_snapshot": restored,
        }
    finally:
        view.close()


def periodic_view():
    view = trajectory_view()
    view.interactions.hbonds.get_buch_hbonds(
        name="before", pbc=True, structure_indices="all", distance_threshold="4 angstroms"
    )
    before = view.interactions.get_analysis("before")
    # Reimage one entire residue of the real trajectory, preserving its internal geometry.
    atoms = msm.select(view.molsys, selection="group_index == 1")
    assert len(atoms) > 1
    system = view.molsys.copy()
    xyz = msm.pyunitwizard.get_value(msm.get(system, coordinates=True), to_unit="nm").copy()
    box = msm.pyunitwizard.get_value(msm.get(system, box=True), to_unit="nm")
    xyz[:, atoms] += box[:, 0, None, :]
    system.structures.coordinates = msm.pyunitwizard.quantity(xyz, "nm")
    system.interactions = {}
    view.apply_system_edit(system)
    with msm.pyunitwizard.context(standard_units=ANGSTROM_POLICY):
        assert str(msm.pyunitwizard.get_unit(msm.get(view.molsys, coordinates=True))) == "angstrom"
        result = view.interactions.hbonds.get_buch_hbonds(
            name="buch", pbc=True, structure_indices="all", distance_threshold="4 angstroms"
        )
        view.interactions.add("buch", tag="real-hb").set_radius("0.2 angstroms")
        expected, _, images = observed_geometry(view, "buch", "real-hb")

    def rows(analysis):
        data = analysis.to_dict()
        return {
            (
                int(frame),
                tuple(int(p["atom_indices"][0]) for p in analysis.relation(int(relation))["participants"]),
            ): float(distance)
            for frame, relation, distance in zip(
                data["structure_indices"], data["relation_indices"], data["measurements"]["distance"]
            )
        }

    old, new = rows(before), rows(result)
    assert old.keys() == new.keys()
    np.testing.assert_allclose(list(old.values()), [new[k] for k in old], atol=1e-8)
    assert images > 0, "Periodic qualification needs observations with nonzero images."
    return view, expected, images


def qualify_periodic(directory, *, browser_fixture=False):
    view, expected, images = periodic_view()
    try:
        restored = round_trips(view, directory)
        report = {
            "case": "periodic-reimaging",
            "atoms": view.molsys.get_n_atoms(),
            "observations": len(expected),
            "nonzero_image_observations": images,
            "policy": "angstrom",
            "controlled_change": "one real residue translated by the first box vector",
        }
        if browser_fixture:
            report.update(
                initial_messages=view._build_embedded_runtime_snapshot(),
                restored_messages=restored,
                series=view.interactions._static_messages(),
                expected=[
                    {"occurrence_index": i, "frame": f, "start_nm": start.tolist(), "end_nm": end.tolist()}
                    for i, (f, start, end) in expected.items()
                ],
            )
        return report
    finally:
        view.close()


def qualify_solvated():
    started = time.perf_counter()
    view = msv.new_view(msm.systems["chicken villin HP35"]["traj_chicken_villin_HP35_solvated.h5msm"])
    try:
        result = view.interactions.hbonds.get_buch_hbonds(name="buch", pbc=True)
        view.interactions.add("buch", tag="real-hb")
        expected, participants, images = observed_geometry(view, "buch", "real-hb")
        query_checks(view, "buch", participants)
        return {
            "case": "solvated-villin",
            "atoms": result.n_atoms,
            "structures": result.n_structures,
            "observations": len(expected),
            "nonzero_image_observations": images,
            "analysis_numeric_bytes": result.numeric_nbytes,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
        }
    finally:
        view.close()


def qualify_disulfides(directory=None):
    view = msv.new_view(msm.systems["2HGR"]["2hgr.pdb"])
    try:
        before = int(msm.get(view.molsys, n_bonds=True))
        before_pairs = np.asarray(msm.get(view.molsys, element="bond", bonded_atom_pairs=True)).copy()
        atoms = msm.select(view.molsys, selection='atom_name == "SG" and group_name == "CYS"')
        xyz = msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm")[0]
        wanted = {
            tuple(sorted((int(a), int(b))))
            for offset, a in enumerate(atoms)
            for b in atoms[offset + 1 :]
            if np.linalg.norm(xyz[a] - xyz[b]) <= 0.205
        }
        result = view.interactions.disulfides.get_disulfide_candidates(name="sulfur", pbc=False)
        actual = {
            tuple(sorted(int(p["atom_indices"][0]) for p in result.relation(i)["participants"]))
            for i in range(len(result.relation_types))
        }
        assert actual == wanted and wanted
        assert int(msm.get(view.molsys, n_bonds=True)) == before
        np.testing.assert_array_equal(msm.get(view.molsys, element="bond", bonded_atom_pairs=True), before_pairs)
        view.interactions.add("sulfur", tag="real-ss")
        expected, _, _ = observed_geometry(view, "sulfur", "real-ss")
        if directory is not None:
            round_trips(view, directory, name="sulfur", tag="real-ss")
        return {
            "case": "2HGR-sulfur-proximity",
            "atoms": result.n_atoms,
            "observations": len(expected),
            "criterion_nm": 0.205,
            "topology_unchanged": True,
            "interpretation": "geometric candidates, not certified covalent bonds",
        }
    finally:
        view.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--browser-fixture", action="store_true")
    args = parser.parse_args()
    provider_root = Path(msm.__file__).resolve().parents[1]

    def git_state():
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=provider_root, capture_output=True, text=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=provider_root, capture_output=True, text=True)
        return {
            "head": head.stdout.strip() if head.returncode == 0 else None,
            "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        }

    provider_before = git_state()
    if args.browser_fixture:
        report = qualify_periodic(args.output_directory, browser_fixture=True)
    else:
        trajectory = qualify_trajectory(args.output_directory / "trajectory")
        trajectory.pop("restored_snapshot")
        report = {
            "provider_version": msm.__version__,
            "provider_source": msm.__file__,
            "viewer_source": msv.__file__,
            "cases": [
                trajectory,
                qualify_periodic(args.output_directory / "periodic"),
                qualify_solvated(),
                qualify_disulfides(args.output_directory / "disulfides"),
            ],
            "peak_process_rss_mib": peak_rss_mib(),
            "provider_before": provider_before,
            "provider_after": git_state(),
        }
    print(json.dumps(_to_plain(report), allow_nan=False))


if __name__ == "__main__":
    main()
