"""Run the actual notebook refinements through the public selection contract."""

import json
from pathlib import Path

import numpy as np

from molsysviewer import demo

ROOT = Path(__file__).resolve().parents[1]


def test_documented_whole_masks_resolve_expressions_before_refining():
    notebook = json.loads((ROOT / "docs/content/user/molecular_system/get.ipynb").read_text(encoding="utf-8"))
    view = demo["181L"]
    namespace = {"view": view}
    try:
        examples = [
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code" and "mask=" in "".join(cell["source"])
        ]
        assert len(examples) == 2
        for source in examples:
            exec(compile(source, "get.ipynb", "exec"), namespace)
        protein_ca = namespace["protein_ca"]
        expected = view.whole.select(selection='molecule_type=="protein" and atom_name=="CA"')
        np.testing.assert_array_equal(protein_ca, expected)
        phenylalanine_ca = view.whole.select(selection=protein_ca, mask=namespace["phe_mask"])
        assert len(phenylalanine_ca) > 0
        names = view.whole.get(element="atom", selection=phenylalanine_ca, group_name=True)
        assert set(names) == {"PHE"}
    finally:
        view.close()
