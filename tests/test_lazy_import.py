from __future__ import annotations

import json
import subprocess
import sys


def test_top_level_import_is_lazy_and_public_api_materializes_on_demand():
    code = r'''
import json
import sys
import molsysviewer as m

before = {
    "demo": "molsysviewer.demo" in sys.modules,
    "viewer": "molsysviewer.viewer" in sys.modules,
    "pyunitwizard": "molsysviewer._pyunitwizard" in sys.modules,
    "config": "molsysviewer.config" in sys.modules,
    "checked_dep": bool(getattr(m, "_checked_dep", False)),
}
materialized = {
    "view": m.MolSysView.__name__,
    "new_view": callable(m.new_view),
    "demo": type(m.demo).__name__,
    "pyunitwizard": m.pyunitwizard.__name__,
    "addon": m.AddonSpec.__name__,
    "config": m.config.__name__,
}
print(json.dumps({"before": before, "materialized": materialized}))
'''

    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["before"] == {
        "demo": False,
        "viewer": False,
        "pyunitwizard": False,
        "config": False,
        "checked_dep": True,
    }
    assert result["materialized"] == {
        "view": "MolSysView",
        "new_view": True,
        "demo": "DemoCatalog",
        "pyunitwizard": "pyunitwizard",
        "addon": "AddonSpec",
        "config": "molsysviewer.config",
    }
