"""Persistent real Python authority for user-origin trajectory-plot navigation."""

import argparse
import json
import sys
from decimal import Decimal, localcontext
from importlib import import_module
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


def precision_controls():
    """Synthetic numeric controls on a real molecular trajectory, not science results."""
    narrow = [1e12 + 0.001, 1e12 + 0.002, 1e12 + 0.003]
    tiny = [0.0001, 0.0002, 0.0005]
    subnormal = float.fromhex("0x0.0000000000001p-1022")
    adjacent = [1.0, float(np.nextafter(1.0, 2.0)), float(np.nextafter(np.nextafter(1.0, 2.0), 2.0))]
    extreme = [
        float(np.nextafter(np.nextafter(sys.float_info.max, 0), 0)),
        float(np.nextafter(sys.float_info.max, 0)),
        sys.float_info.max,
    ]
    return {
        "tiny": {"x": [1.0001, 1.0002, 1.0005], "y": tiny, "unit": "nm"},
        "angstrom": {
            "x": [1.0001, 1.0002, 1.0005],
            "y": puw.get_value(puw.quantity(tiny, "nm"), to_unit="angstrom").tolist(),
            "unit": "Å",
        },
        "signed": {"x": [-2e-8, 0, 2e-8], "y": [-1e-8, 0, 1e-8]},
        "large-offset": {"x": narrow, "y": narrow},
        "negative-offset": {"x": [-value for value in narrow], "y": [-value for value in narrow]},
        "unordered-offset": {"x": [narrow[2], narrow[0], narrow[1]], "y": [narrow[1], narrow[2], narrow[0]]},
        "wide": {"x": [-1e308, 0, 1e308], "y": [-1e308, 0, 1e308]},
        "asymmetric-wide": {
            "x": [-sys.float_info.max, -sys.float_info.max / 2, sys.float_info.max],
            "y": [sys.float_info.max, -sys.float_info.max / 2, -sys.float_info.max],
        },
        "subnormal": {"x": [subnormal, 2 * subnormal, 3 * subnormal], "y": [subnormal, 2 * subnormal, 3 * subnormal]},
        "adjacent": {"x": adjacent, "y": adjacent},
        "lower-notation-threshold": {"x": [float(np.nextafter(0.001, 0)), 0.001, 0.001], "y": [1, 2, 3]},
        "upper-notation-threshold": {"x": [float(np.nextafter(1e6, 0)), 1e6, 1e6], "y": [1, 2, 3]},
        "extreme-adjacent": {"x": extreme, "y": extreme},
        "constant": {"x": [1e300] * 3, "y": [-1e300] * 3},
        "broad": {"x": [0, narrow[0], narrow[1]], "y": [1.234567891e-9, 1.234567892e-9, 1000]},
    }


def decimal_fractions(values):
    """Independent exact-binary64 Decimal oracle, including subnormal/extreme spans."""
    exact = [Decimal.from_float(float(value)) for value in values]
    low, high = min(exact), max(exact)
    if low == high:
        return [0.5] * len(values)
    # Every finite binary64 is exact here, including subtraction of a maximum
    # finite value and a subnormal. Only the final expected fraction becomes float.
    with localcontext() as context:
        context.prec = 2200
        return [float((value - low) / (high - low)) for value in exact]


def serve(static_path=None, state_path=None):
    with msv.demo["pentalanine"] as seed:
        view = msv.new_view(seed.molsys, structure_indices=[0, 8, 3])
    coordinates = puw.get_value(view.get_coordinates(), to_unit="angstrom").copy()
    centered = coordinates - coordinates.mean(axis=1)[:, None]
    values = np.sqrt(np.mean(np.sum(centered**2, axis=2), axis=1))
    view.trajectory_plot.show(
        {"Geometric spread control": values},
        x=[0, 4, 10],
        x_label="Sample coordinate",
        y_label="Spread (Å)",
        title="Native trajectory control",
        tag="authority-plot",
    )
    view.measurements.add_distance([0], [5], tag="plot-distance")
    view.player.go_to_structure(2)
    if static_path is not None:
        view.export.html(static_path)
    callbacks = []
    view.on_frame_change(callbacks.append)
    controls = precision_controls()
    precision_case = None
    state_restored = False

    def inspect(authority, event):
        nonlocal precision_case, state_restored
        action = event.get("plot_fixture")
        if action == "inspect":
            np.testing.assert_array_equal(puw.get_value(authority.get_coordinates(), to_unit="angstrom"), coordinates)
            authority.widget.send(
                {
                    "op": "trajectory_plot_fixture_state",
                    "index": authority.player.index,
                    "is_playing": authority.player.is_playing,
                    "callbacks": list(callbacks),
                    "coordinates": coordinates.tolist(),
                    "plot_count": len(authority.trajectory_plot.records()),
                    "static_path": None if static_path is None else str(static_path),
                    "current_distance": float(
                        puw.get_value(authority.measurements.series("plot-distance"), to_unit="angstrom")[
                            authority.player.index
                        ]
                    ),
                    "precision": None
                    if precision_case is None
                    else {
                        "name": precision_case,
                        **controls[precision_case],
                        "x_fractions": decimal_fractions(controls[precision_case]["x"]),
                        "y_fractions": decimal_fractions(controls[precision_case]["y"]),
                        "records": authority.trajectory_plot.records(),
                        "state_restored": state_restored,
                    },
                }
            )
            return True
        if action == "go":
            authority.player.go_to_structure(event["index"])
            return True
        if action == "snapshot":
            authority.widget.send(
                {"op": "trajectory_plot_fixture_snapshot", "messages": authority._build_embedded_runtime_snapshot()}
            )
            return True
        if action == "precision":
            precision_case = event["case"]
            state_restored = False
            control = controls[precision_case]
            authority.trajectory_plot.clear()
            authority.trajectory_plot.show(
                {"Numeric control": control["y"]},
                x=control["x"],
                x_label="Sample coordinate",
                y_label=f"Numeric control ({control['unit']})" if "unit" in control else "Numeric control",
                title=f"Precision: {precision_case}",
                tag="precision-plot",
                width=650,
            )
            return True
        if action == "restore-precision":
            if precision_case is None or state_path is None:
                raise ValueError("Precision restore requires a selected control and an owned state path")
            before = authority.trajectory_plot.records()
            authority.save_state(state_path)
            document = json.loads(state_path.read_text(encoding="utf-8"))
            assert document["trajectory_plots"] == before
            # Perturb both the data and labels before restoring the actual file.
            authority.trajectory_plot.show(
                {"Perturbed": [42, 43, 44]}, x=[8, 3, 0], title="Perturbed", tag="precision-plot"
            )
            assert authority.trajectory_plot.records() != before
            authority.load_state(state_path)
            assert authority.trajectory_plot.records() == before
            state_restored = True
            return True
        return False

    import_module("canvas-popup-bridge").serve(view, inspect)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--static-path", type=Path)
    parser.add_argument("--state-path", type=Path)
    arguments = parser.parse_args()
    serve(arguments.static_path, arguments.state_path)
