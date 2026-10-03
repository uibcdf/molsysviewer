"""Emit real, calculated family scenes for the Mol* browser qualification.

Run ``python devtools/qualify_interaction_families.py OUTPUT_DIRECTORY`` with
the experimental provider being qualified first on PYTHONPATH. Python tests
independently verify the scientific role/image/centroid projection. This tool
preserves that projection across a session and supplies it to the browser,
which verifies the actual Mol* mesh, group labels and occurrence identities.
"""

import json
import os
import sys
from pathlib import Path
from runpy import run_path

ROOT = Path(__file__).resolve().parents[1]
if os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") != "1":
    sys.path.insert(0, str(ROOT))
else:
    run_path(str(ROOT / "devtools/_fixture_namespace.py"))["expose_fixture_namespace"](ROOT)

import molsysmt as msm  # noqa: E402
from devtools.interaction_family_fixtures import make_family_view  # noqa: E402
from molsysviewer._private.interaction_families import FAMILIES  # noqa: E402

import molsysviewer as msv  # noqa: E402


def browser_fixtures(directory):
    """Calculate all nine families and both supported water mediator orders."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cases = []
    for kind in list(FAMILIES) + ["water_bridge_2"]:
        periodic = kind not in {"hbond", "disulfide_candidate"}
        case = make_family_view(kind, periodic=periodic)
        view = case.view
        restored = None
        try:
            result = case.calculate(pbc=periodic)
            if not result.n_interactions:
                raise AssertionError(f"The real detector did not produce the positive {kind} fixture.")
            view.interactions.add("contacts", tag="family")
            expected = view.interactions._messages(0)[0]
            if expected["n_supported"] != result.n_interactions or expected["n_skipped"]:
                raise AssertionError(f"The {kind} fixture is not completely projected.")
            path = directory / f"{kind}.msvz"
            view.save_session(path)
            restored = msv.load_session(path)
            cases.append(
                {
                    "kind": kind,
                    "periodic": periodic,
                    "expected": expected,
                    "initial_messages": view._build_embedded_runtime_snapshot(),
                    "restored_messages": restored._build_embedded_runtime_snapshot(),
                }
            )
        finally:
            view.close()
            if restored is not None:
                restored.close()
    return {
        "provider_version": msm.__version__,
        "viewer_version": msv.__version__,
        "scientific_module_paths": {"molsysmt": msm.__file__, "molsysviewer": msv.__file__},
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(browser_fixtures(sys.argv[1])))
