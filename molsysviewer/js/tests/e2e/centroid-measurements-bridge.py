"""Real pentalanine measurements and independent coordinate oracles for Chromium."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


def new_view():
    with msv.demo["pentalanine"] as seed:
        view = msv.new_view(seed.molsys, structure_indices=[0, 8, 3])
    specifications = [
        ("distance", "centroid-distance", [[0, 2, 4], [5]], "centroid"),
        ("distance", "repeated-distance", [[0, 0, 2, 4], [5]], "centroid"),
        ("angle", "centroid-angle", [[0, 2, 4], [5, 6, 7], [9, 11, 12]], "centroid"),
        ("dihedral", "centroid-dihedral", [[0, 2, 4], [5, 6, 7], [9, 11, 12], [18, 21, 25]], "centroid"),
        ("distance", "atomic-distance", [[0], [5]], "atom"),
        ("distance", "representative-distance", [[0, 2, 4], [5, 6, 7]], "representative_atom"),
    ]
    for kind, tag, endpoints, policy in specifications:
        getattr(view.measurements, f"add_{kind}")(
            *endpoints,
            tag=tag,
            endpoint_policy=policy,
            measurement_style={"color": "#ab1234", "size_em": 1.7, "background": True, "background_opacity": 0.6},
        )
    return view, specifications


def oracle(view, specifications):
    coordinates = np.asarray(puw.get_value(view.get_coordinates(), to_unit="angstrom"))
    records = []
    for kind, tag, endpoints, policy in specifications:
        # These representative populations contain no preferred CA/P; the
        # documented fallback is their first atom, independently of summaries.
        effective = endpoints if policy == "centroid" else [atoms[:1] for atoms in endpoints]
        points = np.stack([coordinates[:, atoms].mean(axis=1) for atoms in effective], axis=1)
        if kind == "distance":
            values = np.linalg.norm(points[:, 1] - points[:, 0], axis=1)
        elif kind == "angle":
            a, b = points[:, 0] - points[:, 1], points[:, 2] - points[:, 1]
            cosine = np.einsum("ij,ij->i", a, b) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
            values = np.degrees(np.arccos(np.clip(cosine, -1, 1)))
        else:
            # Signed torsion from projected bonds, independent of Viewer and Mol*.
            axis = points[:, 2] - points[:, 1]
            axis /= np.linalg.norm(axis, axis=1)[:, None]
            a, b = points[:, 0] - points[:, 1], points[:, 3] - points[:, 2]
            a -= np.einsum("ij,ij->i", a, axis)[:, None] * axis
            b -= np.einsum("ij,ij->i", b, axis)[:, None] * axis
            values = np.degrees(np.arctan2(np.einsum("ij,ij->i", np.cross(axis, a), b), np.einsum("ij,ij->i", a, b)))
        records.append(
            {
                "kind": kind,
                "tag": tag,
                "endpoints": endpoints,
                "effective": effective,
                "policy": policy,
                "points": points.tolist(),
                "values": values.tolist(),
                "python_series": puw.get_value(
                    view.measurements.series(tag), to_unit="angstrom" if kind == "distance" else "degrees"
                ).tolist()
                if view.measurements.contains(tag)
                else None,
            }
        )
    return {"coordinates": coordinates.tolist(), "measurements": records}


def fixture():
    # The payload always promises Å/degrees even under another application policy.
    with puw.context(standard_units=["pm", "ps", "radian"]):
        view, specifications = new_view()
        try:
            payload = {"initial": view._build_embedded_runtime_snapshot(), "before": oracle(view, specifications)}
            sent = []
            view._ready = True
            view.widget.send = sent.append
            stages = []

            def stage(name, operation):
                sent.clear()
                operation()
                stages.append({"name": name, "messages": list(sent), "oracle": oracle(view, specifications)})

            stage("hide", lambda: view.measurements.hide("centroid-distance"))
            stage("show", lambda: view.measurements.show("centroid-distance"))
            specifications[0] = (*specifications[0][:1], "renamed-distance", *specifications[0][2:])
            stage("rename", lambda: view.measurements.set_tag("centroid-distance", "renamed-distance"))
            coordinates = puw.get_value(view.get_coordinates(structure_indices=[2, 0]), to_unit="angstrom")[
                :, [0, 2, 4]
            ].copy()
            coordinates += np.array([1.3, -0.6, 0.9])
            stage(
                "coordinates",
                lambda: view.partial_coordinates_update(
                    puw.quantity(coordinates, "angstrom"),
                    selection=[0, 2, 4],
                    structure_indices=[2, 0],
                    transaction_id="centroids",
                ),
            )
            stage("delete", lambda: view.measurements.delete("renamed-distance"))
            stage("undo", view.history.undo)
            payload["stages"] = stages
            with tempfile.TemporaryDirectory(prefix="msv-centroid-session-") as directory:
                path = Path(directory) / "centroids.msv"
                view.save_session(path)
                with msv.load_session(path) as restored:
                    payload["session"] = restored._build_embedded_runtime_snapshot()
                    payload["session_oracle"] = oracle(restored, specifications)
            return payload
        finally:
            view.close()


if __name__ == "__main__":
    if "--popup" in sys.argv:
        from importlib import import_module

        def inspect(authority, event):
            if event.get("measurement_fixture") == "inspect":
                authority._sync_measurement_summaries_runtime()
                return True
            return False

        with puw.context(standard_units=["pm", "ps", "radian"]):
            view, _ = new_view()
            import_module("canvas-popup-bridge").serve(view, inspect)
    else:
        print(json.dumps(fixture()))
