"""Installed-artifact collection must not depend on pytest's prepend mode."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_edit_helper_consumers_import_without_the_tests_directory_on_sys_path(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = """
import importlib
import importlib.util
import sys
from pathlib import Path

directory = Path(sys.argv[1]) / 'tests'
assert directory not in [Path(path).resolve() for path in sys.path]
spec = importlib.util.spec_from_file_location('tests', directory / '__init__.py',
                                            submodule_search_locations=[str(directory)])
package = importlib.util.module_from_spec(spec)
sys.modules['tests'] = package
spec.loader.exec_module(package)
for module in ('test_selections', 'test_protocol_contracts', 'test_live_edit_rebuild',
               'test_rebuild_persistence', 'test_rebuild_visibility', 'test_region_recipes',
               'test_reproducible_interaction', 'test_view_lifecycle',
               'test_teardown_leaves_no_widget_registered', 'test_addons'):
    imported = importlib.import_module('tests.' + module)
    assert Path(imported.__file__).parent == directory
assert Path(sys.modules['tests._edit_helpers'].__file__).parent == directory
assert Path(sys.modules['tests.conftest'].__file__).parent == directory
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(root)], cwd=tmp_path, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") != "1", reason="Requires installed scientific artifacts"
)
def test_installed_qualification_uses_own_metadata_and_rejects_source_modules(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = """
import importlib.metadata
import importlib.util
import sys
from pathlib import Path

import molsysmt
import molsysviewer
root = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('installed_runner', root / 'devtools/qualify_installed_interactions.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
expected = {name: importlib.metadata.version(name) for name in ('molsysmt', 'molsysviewer')}
runner.verify_imports(expected)

# A real competing metadata record must not override the interpreter's artifact.
shadow = Path(sys.argv[2]) / 'metadata'
record = shadow / 'molsysmt-0.0.1.dist-info'
record.mkdir(parents=True)
(record / 'METADATA').write_text('Metadata-Version: 2.1\\nName: molsysmt\\nVersion: 0.0.1\\n')
sys.path.insert(0, str(shadow))
assert importlib.metadata.version('molsysmt') == '0.0.1'
runner.verify_imports(expected)

# Execute an actual source implementation under its scientific module name.
name = 'molsysviewer.new_view'
spec = importlib.util.spec_from_file_location(name, root / 'molsysviewer/new_view.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules[name] = module
try:
    runner.verify_imports(expected)
except ValueError as error:
    assert name in str(error) and 'outside' in str(error), str(error)
else:
    raise AssertionError('The installed guard accepted a scientific source import.')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(root), str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_scientific_fixture_tools_preserve_package_discovery_in_installed_mode(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = """
import importlib
import importlib.metadata
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

os.environ['MOLSYSVIEWER_TEST_INSTALLED'] = '1'
import molsysmt
import molsysviewer
root = Path(sys.argv[1]).resolve()
assert str(root) not in sys.path
versions = {name: importlib.metadata.version(name) for name in ('molsysmt', 'molsysviewer')}
origins = {name: sys.modules[name].__file__ for name in versions}
namespace = ModuleType('devtools')
namespace.__path__ = [str(root / 'devtools')]
namespace.__spec__ = importlib.util.spec_from_loader('devtools', loader=None, is_package=True)
sys.modules['devtools'] = namespace
for name in ('devtools.benchmarks.interactions_residency',
             'devtools.benchmarks.interactions_detector',
             'devtools.qualify_interactions', 'devtools.qualify_interaction_families'):
    importlib.import_module(name)
    assert str(root) not in sys.path, name
    for package, version in versions.items():
        assert importlib.metadata.version(package) == version, name
        assert sys.modules[package].__file__ == origins[package], name
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(root)], cwd=tmp_path, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") != "1", reason="Requires installed scientific artifacts"
)
def test_direct_family_cli_uses_installed_science_without_checkout_on_sys_path(tmp_path):
    import molsysmt

    import molsysviewer

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", str(root / "devtools/qualify_interaction_families.py"), str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["provider_version"] == molsysmt.__version__
    assert report["viewer_version"] == molsysviewer.__version__
    assert report["scientific_module_paths"] == {"molsysmt": molsysmt.__file__, "molsysviewer": molsysviewer.__file__}
    assert len(report["cases"]) == 10
    assert all(case["expected"]["n_supported"] > 0 for case in report["cases"])
