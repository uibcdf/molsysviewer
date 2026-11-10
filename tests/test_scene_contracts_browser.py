"""Explicit browser receiving of real structure-scoped scene contracts."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_SCENE_CONTRACT_TEST") != "1",
    reason="Explicit qualified-browser receiving; core E2E runs the same scenario",
)
def test_dynamic_memberships_follow_native_frames_and_reject_stale_packets():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", str(root / "molsysviewer/js/tests/e2e/scene-contracts.e2e.js")],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "native three-structure memberships" in result.stdout
    assert "stale packets refused" in result.stdout
