"""Public scene modules and reference entries must resolve from a cold process."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", ["molsysviewer.layers", "molsysviewer.shapes", "molsysviewer.interactions"])
def test_cold_public_scene_imports(module):
    code = f"""
import importlib
import sys
importlib.import_module({module!r})
assert 'molsysviewer.viewer.core' not in sys.modules
import molsysviewer as msv
from molsysviewer.viewer import MolSysView
assert msv.MolSysView is MolSysView
assert msv.new_view
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_public_reference_entries_resolve_in_a_fresh_process():
    text = (ROOT / "docs/api/public/api_public.rst").read_text()
    entries = re.findall(r"^ +molsysviewer(?:\.[A-Za-z_][A-Za-z0-9_]*)+ *$", text, re.MULTILINE)
    entries = [entry.strip() for entry in entries]
    assert entries
    code = """
import importlib
import json
import sys
for entry in json.loads(sys.argv[1]):
    parts = entry.split('.')
    for length in range(len(parts), 0, -1):
        prefix = '.'.join(parts[:length])
        try:
            value = importlib.import_module(prefix)
        except ModuleNotFoundError as error:
            if error.name != prefix and not prefix.startswith(error.name + '.'):
                raise
            continue
        for attribute in parts[length:]:
            value = getattr(value, attribute)
        break
    else:
        raise AssertionError('Unresolved public reference: ' + entry)
"""
    result = subprocess.run([sys.executable, "-c", code, json.dumps(entries)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_representation_guide_links_resolve():
    page = ROOT / "docs/content/user/representations/types.md"
    links = re.findall(r"\{doc\}`([^`]+)`", page.read_text())
    assert links
    for link in links:
        target = (page.parent / link).resolve()
        assert any(target.with_suffix(suffix).exists() for suffix in (".md", ".ipynb", ".rst")), link
