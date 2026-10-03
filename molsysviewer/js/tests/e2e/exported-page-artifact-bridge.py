"""Produce actual HTML artifacts with independently checked periodic links."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from devtools.qualify_interactions import periodic_view
from molsysviewer._pyunitwizard import puw


def main():
    output = Path(tempfile.mkdtemp(prefix="msv-html-artifacts-"))
    assets = output / "assets"
    assets.mkdir()
    view, expected, images = periodic_view()
    with view:
        view.whole.set_representation("ball_and_stick")
        view.regions.add(atom_indices=[0, 1], tag="saved-region", representation="spacefill").hide()
        view.annotations.add("HTML label", atom_indices=[0], tag="saved-label")
        view.measurements.add_distance([0], [1], tag="saved-distance")
        view.shapes.add_sphere(center=puw.quantity([0, 0, 0], "nm"), radius="0.2 nm", tag="saved-sphere")
        view.selections.add("saved-selection", atom_indices=[0, 1])
        view.active_selection.set([0, 1])
        view.player.go_to_structure(2)
        view.export.html(str(output / "inline.html"))
        view.export.html(str(output / "view #1 %.html"), shared_runtime=str(assets), inline_messages=False)
        print(json.dumps({
            "directory": str(output), "atoms": view.molsys.get_n_atoms(), "images": images,
            "expected": [{"occurrence": occurrence, "frame": frame, "start": start.tolist(), "end": end.tolist()}
                         for occurrence, (frame, start, end) in expected.items()],
        }))


if __name__ == "__main__":
    main()
