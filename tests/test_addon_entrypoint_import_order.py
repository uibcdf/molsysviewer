"""Exercise real import machinery and entry-point metadata in fresh processes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _provider(tmp_path: Path, *, deferred: bool, callable_entry: bool) -> None:
    declaration = (
        "def make_spec():\n"
        "    global calls\n"
        "    calls += 1\n"
        '    return AddonSpec(name="review-import-order", panels=(panel,))\n'
        if callable_entry
        else 'addon = AddonSpec(name="review-import-order", panels=(panel,))\n'
    )
    (tmp_path / "review_import_order.py").write_text(
        "from molsysviewer import AddonSpec, AddonPanelSpec, AddonLifecycleSpec, MolSysView\n"
        + ('from molsysviewer import addons\naddons.discover(modules=["review_import_order"])\n' if deferred else "")
        + "calls = 0\n"
        + 'panel = AddonPanelSpec(id="review", title="Review", entry="review.panel")\n'
        + declaration
        + "def on_enable(view):\n    view.review_enabled = True\n"
        + "def on_disable(view):\n    view.review_enabled = False\n",
        encoding="utf-8",
    )
    (tmp_path / "review_invalid_contract.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "review_ready_provider.py").write_text(
        "from molsysviewer import AddonSpec\ncalls = 0\n"
        "def make_spec():\n    global calls\n    calls += 1\n"
        '    return AddonSpec(name="review-ready-provider")\n',
        encoding="utf-8",
    )
    (tmp_path / "review_broken_import.py").write_text('raise RuntimeError("review real import failure")\n')
    metadata = tmp_path / "review_import_order-0.1.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text("Metadata-Version: 2.1\nName: review-import-order\nVersion: 0.1\n")
    target = "review_import_order:make_spec" if callable_entry else "review_import_order"
    (metadata / "entry_points.txt").write_text(
        f"[molsysviewer.addons]\nreview-import-order = {target}\n"
        "review-ready-provider = review_ready_provider:make_spec\n"
        "review-invalid-contract = review_invalid_contract\n"
        "review-broken-import = review_broken_import\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("import_order", ["addon", "types", "registry"])
@pytest.mark.parametrize("callable_entry", [False, True])
@pytest.mark.parametrize("deferred", [False, True])
def test_root_specs_register_complete_entrypoints_without_false_import_failures(
    tmp_path, import_order, callable_entry, deferred
):
    _provider(tmp_path, deferred=deferred, callable_entry=callable_entry)
    first_import = {
        "addon": "",
        "types": "from molsysviewer import MolSysView, AddonSpec",
        "registry": "from molsysviewer import addons",
    }[import_order]
    code = f"""
import sys, json
sys.path[:0] = [{str(tmp_path)!r}, {str(ROOT)!r}]
{first_import}
import review_import_order as provider
import molsysviewer as msv
registry = msv.addons
assert registry.contains("review-import-order")
assert registry.get("review-import-order").panels[0].id == "review"
failures = {{item["source"]: item for item in registry.discovery_failures()}}
assert "entry-point:review-import-order" not in failures
assert "valid add-on contract" in failures["entry-point:review-invalid-contract"]["reason"]
assert "review real import failure" in failures["entry-point:review-broken-import"]["reason"]
assert "RuntimeError" in failures["entry-point:review-broken-import"]["traceback"]
assert registry.lifecycle_for("review-import-order").on_enable is provider.on_enable
views = [msv.MolSysView(), msv.MolSysView()]
try:
    assert all(view.review_enabled for view in views)
    assert all("review-import-order" in view.addons.available() for view in views)
finally:
    for view in views:
        view.close()
assert all(not view.review_enabled for view in views)
assert provider.calls == {1 if callable_entry else 0}
import review_ready_provider
assert review_ready_provider.calls == 1
assert registry.contains("review-ready-provider")
assert not any(item["source"] == "entry-point:review-ready-provider" for item in registry.discovery_failures())
assert not any(item["source"] == "entry-point:review-import-order" for item in registry.discovery_failures())
print(json.dumps({{"registered": True, "factory_calls": provider.calls}}))
"""
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout.splitlines()[-1])["registered"] is True


def test_constructing_view_discovers_entrypoints_without_accessing_root_registry(tmp_path):
    _provider(tmp_path, deferred=False, callable_entry=True)
    code = f"""
import sys
sys.path[:0] = [{str(tmp_path)!r}, {str(ROOT)!r}]
from molsysviewer import MolSysView
view = MolSysView()
try:
    assert "review-import-order" in view.addons.available()
    assert view.review_enabled
finally:
    view.close()
"""
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_explicit_registry_clear_remains_empty_until_explicit_rediscovery(tmp_path):
    _provider(tmp_path, deferred=False, callable_entry=True)
    code = f"""
import sys
sys.path[:0] = [{str(tmp_path)!r}, {str(ROOT)!r}]
import molsysviewer as msv
registry = msv.addons
assert registry.contains("review-import-order")
registry.clear()
assert msv.addons.names() == []
view = msv.MolSysView()
try:
    assert view.addons.available() == []
    assert not hasattr(view, "review_enabled")
finally:
    view.close()
registry.discover()
assert registry.contains("review-import-order")
"""
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
