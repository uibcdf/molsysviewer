"""Emit a canonical static-export projection for the real-Mol* E2E."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import molsysmt as msm
import pyunitwizard as puw

from molsysviewer import MolSysView


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    view = MolSysView()
    source = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]
    view.load(source, structure_indices=[0, 1])
    view.whole.set_representation(
        "ball_and_stick",
        quality="medium",
        skip_digestion=True,
    )
    region = view.regions.add(
        "atom_index < 6",
        tag="exported-region",
        representation="spacefill",
        quality="high",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)
    view.annotations.add_annotation(
        "Exported label",
        atom_indices=[0],
        tag="exported-label",
        skip_digestion=True,
    )
    view.measurements.add_distance(
        [0],
        [1],
        tag="exported-distance",
        skip_digestion=True,
    )
    view.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="exported-shape",
        skip_digestion=True,
    )
    view.selections.add("exported-selection", atom_indices=[0, 1])
    view.player.go_to_structure(1, skip_digestion=True)
    view.camera.set_snapshot(
        {
            "target": [0.0, 0.0, 0.0],
            "position": [30.0, 30.0, 30.0],
            "up": [0.0, 1.0, 0.0],
        },
        skip_digestion=True,
    )

    document = {
        "messages": view._build_export_messages(),  # noqa: SLF001
        "expected": {
            "atomCount": 62,
            "frame": 1,
            "wholeRepresentation": "ball-and-stick",
            "regionRepresentation": "spacefill",
            "regionHidden": True,
            "annotationTag": "exported-label",
            "measurementTag": "exported-distance",
            "shapeTag": "exported-shape",
        },
    }
    args.output.write_text(json.dumps(document, separators=(",", ":")), encoding="utf-8")
    view.close()


if __name__ == "__main__":
    main()
