"""Explicit real-browser receiving of native source/model atom correspondence."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_SOURCE_INDEX_TEST") != "1",
    reason="Explicit qualified-browser receiving; core E2E also runs this scenario",
)
def test_real_source_atom_correspondence_and_recovered_geometry():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", str(root / "molsysviewer/js/tests/e2e/source-atom-indices.e2e.js")],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SOURCE_ATOM_INDICES_OK" in result.stdout
