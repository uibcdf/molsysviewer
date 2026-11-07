"""Persistent real Python authority for user-origin trajectory-plot navigation."""

import argparse
import sys
from importlib import import_module
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


def serve(static_path=None):
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

    def inspect(authority, event):
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
        return False

    import_module("canvas-popup-bridge").serve(view, inspect)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--static-path", type=Path)
    serve(parser.parse_args().static_path)
