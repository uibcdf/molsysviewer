"""Real child probes retain HTML through async reads and then clean it (#178)."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests import test_standalone

REAL_RUN = subprocess.run
PROBES = [
    test_standalone.test_qt_event_transport_smoke_real_qt,
    test_standalone.test_qt_payload_refs_replace_across_two_real_generations,
]

# Observe the original NamedTemporaryFile or the new parent-supplied path.
# Qt, bridge code and the positive transport assertions remain real.
OBSERVE = """
import json, os, pathlib, sys, tempfile
receipt = pathlib.Path(os.environ['QT_PROBE_RESOURCE_RECEIPT'])
def record(path):
    receipt.write_text(json.dumps({'path': str(path)}))
if len(sys.argv) > 1:
    record(sys.argv[1])
else:
    original_file = tempfile.NamedTemporaryFile
    def observed_file(*args, **kwargs):
        handle = original_file(*args, **kwargs)
        record(handle.name)
        return handle
    tempfile.NamedTemporaryFile = observed_file
"""


def instrument(monkeypatch, tmp_path, outcome):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    receipt = tmp_path / "caller-receipt.json"
    monkeypatch.setattr(tempfile, "tempdir", str(workspace))
    monkeypatch.setenv("TMPDIR", str(workspace))
    monkeypatch.setenv("TEMP", str(workspace))
    monkeypatch.setenv("TMP", str(workspace))
    monkeypatch.setenv("QT_PROBE_RESOURCE_RECEIPT", str(receipt))
    children = []
    popen = subprocess.Popen

    def observe_child(*args, **kwargs):
        child = popen(*args, **kwargs)
        children.append(child)
        return child

    def run(command, **kwargs):
        assert kwargs["timeout"] == 90
        assert kwargs["capture_output"] and kwargs["text"]
        command = list(command)
        script = command[2]
        if outcome == "failure":
            script = script.replace(
                "view.setUrl(", "raise RuntimeError('controlled HTML probe failure')\nview.setUrl(", 1
            )
        elif outcome == "timeout":
            script = script.replace("view.setUrl(", "time.sleep(30)\nview.setUrl(", 1)
            kwargs["timeout"] = 10
        command[2] = OBSERVE + script
        return REAL_RUN(command, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", observe_child)
    monkeypatch.setattr(subprocess, "run", run)
    return workspace, receipt, children


@pytest.mark.parametrize("probe", PROBES, ids=["transport", "generations"])
@pytest.mark.parametrize("outcome", ["success", "failure", "timeout"])
def test_html_removed_after_real_child_outcome(monkeypatch, tmp_path, probe, outcome):
    workspace, receipt, children = instrument(monkeypatch, tmp_path, outcome)
    if outcome == "failure":
        with pytest.raises(AssertionError, match="controlled HTML probe failure"):
            probe()
    elif outcome == "timeout":
        with pytest.raises(subprocess.TimeoutExpired):
            probe()
    else:
        probe()
    assert children and all(child.poll() is not None for child in children)
    assert receipt.exists(), "caller evidence must survive"
    html = Path(json.loads(receipt.read_text())["path"])
    assert not html.exists()
    assert workspace.exists() and not list(workspace.iterdir())


@pytest.mark.parametrize("probe", PROBES, ids=["transport", "generations"])
def test_removal_error_visible_after_real_child_finished(monkeypatch, tmp_path, probe):
    workspace, receipt, children = instrument(monkeypatch, tmp_path, "success")

    def remove(cls, name, **kwargs):
        assert children and all(child.poll() is not None for child in children)
        raise PermissionError("controlled HTML removal failure")

    monkeypatch.setattr(tempfile.TemporaryDirectory, "_rmtree", classmethod(remove))
    with pytest.raises(PermissionError, match="controlled HTML removal failure"):
        probe()
    assert receipt.exists() and list(workspace.iterdir())
