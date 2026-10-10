"""Execute the examples actually displayed by Studio, with real geometry."""

import json
import re
from pathlib import Path

import numpy as np
import pytest

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw

SOURCE = Path(__file__).resolve().parents[1] / "molsysviewer/js/src/ui/panels/shapes-panel.ts"
SNIPPETS = [
    json.loads('"' + snippet + '"') for snippet in re.findall(r'codeSnippet: "((?:[^"\\]|\\.)*)"', SOURCE.read_text())
]


@pytest.mark.parametrize("snippet", SNIPPETS)
def test_studio_catalog_example_creates_a_shape(snippet):
    view = msv.demo["pentalanine"]
    try:
        context = {
            "view": view,
            "centers": puw.quantity([[0, 0, 0]], "nm"),
            "radii": puw.quantity([0.2], "nm"),
            "normals": [[0, 0, 1]],
            "kinds": ["donor"],
            "tensors": [np.diag([0.01, 0.02, 0.03]).tolist()],
            "path_points": puw.quantity([[0, 0, 0], [0.1, 0.2, 0.3]], "nm"),
            "tetra_coords": puw.quantity([[[0, 0, 0], [0.2, 0, 0], [0, 0.2, 0], [0, 0, 0.2]]], "nm"),
            "triangle_vertices": puw.quantity([[[0, 0, 0], [0.2, 0, 0], [0, 0.2, 0]]], "nm"),
        }
        if "channel_tube" in snippet:
            context["radii"] = puw.quantity([0.2, 0.2], "nm")
        exec(snippet, context)
        assert view.shapes.count() == 1
        assert view.export_state()["shapes"]
    finally:
        view.close()


def test_all_nine_supplied_geometry_examples_are_exercised():
    assert len(SNIPPETS) == 9
