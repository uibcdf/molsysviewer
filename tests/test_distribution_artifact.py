from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

import molsysviewer as molsysviewer_package

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RUNTIME_DEPENDENCIES = {
    "anywidget",
    "argdigest",
    "depdigest",
    "molsysmt",
    "numpy",
    "packaging",
    "pyunitwizard",
    "smonitor",
    "traitlets",
}
REQUIRED_RUNTIME_RESOURCES = {
    "molsysviewer/runtime_actions.json",
    "molsysviewer/viewer.js",
}


def _dependency_names(requirements: list[str]) -> set[str]:
    return {canonicalize_name(Requirement(item).name) for item in requirements}


def _conda_run_dependencies(recipe: str) -> set[str]:
    match = re.search(r"(?ms)^requirements:\n.*?^  run:\n(?P<body>(?:    .*\n)+)", recipe)
    assert match is not None, "The conda recipe has no requirements.run block"
    names = set()
    for line in match.group("body").splitlines():
        item = line.strip()
        if not item.startswith("- "):
            continue
        name = re.split(r"[ <>=!]", item[2:].split("#", 1)[0].strip(), maxsplit=1)[0]
        names.add(canonicalize_name(name))
    return names


def _copy_wheel_source(destination: Path) -> None:
    shutil.copy2(ROOT / "pyproject.toml", destination / "pyproject.toml")
    shutil.copy2(ROOT / "README.md", destination / "README.md")
    shutil.copytree(
        ROOT / "molsysviewer",
        destination / "molsysviewer",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules", "viewer.js.map"),
    )


def test_distribution_manifests_name_runtime_dependencies_and_resources():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    wheel_dependencies = _dependency_names(pyproject["project"]["dependencies"])
    assert REQUIRED_RUNTIME_DEPENDENCIES <= wheel_dependencies

    package_data = set(pyproject["tool"]["setuptools"]["package-data"]["molsysviewer"])
    assert {"runtime_actions.json", "viewer.js"} <= package_data

    recipe = (ROOT / "devtools" / "conda-build" / "meta.yaml").read_text(encoding="utf-8")
    assert REQUIRED_RUNTIME_DEPENDENCIES <= _conda_run_dependencies(recipe)


def test_built_wheel_imports_from_packaged_runtime_manifest(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _copy_wheel_source(source)

    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(dist)],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]

    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        assert REQUIRED_RUNTIME_RESOURCES <= members
        assert not any(name.startswith("molsysviewer/js/") for name in members)
        metadata_paths = [name for name in members if name.endswith(".dist-info/METADATA")]
        assert len(metadata_paths) == 1
        metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))
        wheel_dependencies = _dependency_names(metadata.get_all("Requires-Dist", []))
        assert REQUIRED_RUNTIME_DEPENDENCIES <= wheel_dependencies

    site = tmp_path / "site"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(site), str(wheel)],
        check=True,
        capture_output=True,
        text=True,
    )
    check_script = """
import json
from importlib.resources import files
from pathlib import Path

import molsysviewer
from molsysviewer.runtime_contract import ACTION_CATEGORIES

site = Path(__import__('os').environ['MSV_TEST_SITE']).resolve()
package = Path(molsysviewer.__file__).resolve()
assert package.is_relative_to(site), (package, site)
manifest = files('molsysviewer').joinpath('runtime_actions.json')
data = json.loads(manifest.read_text(encoding='utf-8'))
assert data['actions']
assert ACTION_CATEGORIES == data['actions']
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(site)
    env["MSV_TEST_SITE"] = str(site)
    subprocess.run(
        [sys.executable, "-c", check_script],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_every_declared_console_script_resolves():
    """A declared entry point that imports nothing is only discovered by a user.

    `pip install` writes the launcher from `pyproject.toml` without ever importing the
    target, so a module that moves or is renamed leaves a command on the user's PATH that
    fails at the first invocation, with no test and no build step objecting.

    This was reported as a defect against `molsysviewer-qt`, whose target reads
    `molsysviewer.standalone_qt:main`, on the evidence that `molsysviewer/standalone_qt.py`
    is not in the tree. It is not: the module became the package `standalone_qt/`, and the
    entry point resolves. Nothing had checked either way, which is the real finding.
    """
    scripts = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["scripts"]

    assert scripts, "no console scripts are declared"

    for command, target in sorted(scripts.items()):
        module_name, separator, attribute = target.partition(":")
        assert separator, f"{command} declares {target!r} without an attribute"

        module = importlib.import_module(module_name)
        entry = getattr(module, attribute, None)

        assert callable(entry), (
            f"the {command!r} console script points at {target!r}, which does not resolve "
            "to a callable"
        )


def test_every_publicly_exported_name_resolves():
    """`__all__` is a promise, and the lazy re-exports here can break it silently.

    `create_standalone_qt0_window` and `launch_standalone_qt0` import their real
    implementation inside the function body, so a missing target raises only when someone
    calls them. Listing a name that cannot be produced is the packaging defect; calling
    each one is not this test's business.
    """
    missing = [name for name in molsysviewer_package.__all__
               if not hasattr(molsysviewer_package, name)]

    assert missing == [], f"names in __all__ that do not resolve: {missing}"
