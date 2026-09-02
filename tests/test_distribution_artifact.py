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
REQUIRED_RUNTIME_VERSION_FLOORS = {
    "argdigest": "0.12.1",
    "molsysmt": "0.22.0",
}


def _dependency_names(requirements: list[str]) -> set[str]:
    return {canonicalize_name(Requirement(item).name) for item in requirements}


def _dependencies_by_name(requirements: list[str]) -> dict[str, Requirement]:
    parsed = (Requirement(item) for item in requirements)
    return {canonicalize_name(item.name): item for item in parsed}


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


def test_every_floor_the_wheel_declares_survives_into_the_conda_recipe():
    """Derived, not enumerated: the pair above pins two floors by name, and four others
    had quietly gone missing from the recipe while `pyproject.toml` still declared them.

    A conda user could therefore resolve `smonitor` below 0.13.0 and import a build whose
    catalog classes take their arguments in the other order -- the wheel refused that
    combination and the conda package accepted it. Enumerating floors is what let the
    drift happen, so this asks the manifests about each other instead.

    Reported against a sibling package as uibcdf/molsysmt#193 before it was noticed here.
    """
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    wheel_requirements = _dependencies_by_name(pyproject["project"]["dependencies"])
    recipe = (ROOT / "devtools" / "conda-build" / "meta.yaml").read_text(encoding="utf-8")

    missing = []
    for name, requirement in wheel_requirements.items():
        floor = next(
            (spec.version for spec in requirement.specifier if spec.operator == ">="), None
        )
        if floor is None:
            continue
        if not re.search(rf"(?m)^\s*-\s+{re.escape(name)}\s+>={re.escape(floor)}\b", recipe):
            missing.append(f"{name}>={floor}")

    assert missing == [], (
        "the conda recipe does not carry these floors that pyproject.toml declares, so "
        f"conda would resolve combinations the wheel refuses: {missing}"
    )


def test_distribution_manifests_bound_the_shared_alias_contract():
    """A resolver-valid dependency set must also be import-compatible.

    ArgDigest 0.12.0 rejects self-aliases. MolSysMT 0.12.0 still exposed the identity
    entry ``constraints -> constraints``, and MolSysViewer imports that alias catalogue
    while constructing its own caller-scoped tables. With no floors in either manifest,
    the resolver admitted a combination that failed during ``import molsysviewer``.
    """
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    wheel_requirements = _dependencies_by_name(pyproject["project"]["dependencies"])

    recipe = (ROOT / "devtools" / "conda-build" / "meta.yaml").read_text(encoding="utf-8")
    for dependency, floor in REQUIRED_RUNTIME_VERSION_FLOORS.items():
        assert str(wheel_requirements[dependency].specifier) == f">={floor}"
        assert re.search(
            rf"(?m)^\s*-\s+{re.escape(dependency)}\s+>={re.escape(floor)}\s*$",
            recipe,
        ), f"the Conda recipe does not require {dependency}>={floor}"


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


SUPPORTED_PYTHON_VERSIONS = ("3.11", "3.12", "3.13")
#: The one we recommend, develop and document on. It is the newest supported
#: version, and it is what the single-version jobs and the README badge must say.
RECOMMENDED_PYTHON_VERSION = "3.13"


def _matrix_versions(workflow: str, pattern: str) -> set[str]:
    text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    return set(re.findall(pattern, text))


def test_the_published_python_matrix_is_the_one_we_actually_test():
    """Three files decide which Pythons we support, and nothing kept them together.

    They had drifted in both directions at once: `requires-python` and the classifiers
    advertised 3.10 while CI tested only 3.11 and 3.12 — and the conda workflow *built and
    published* a 3.10 artifact that no test job ever ran. Meanwhile 3.13, the version
    development happens on, appeared in none of them, so `>=3.10` let users install it
    untested.

    A wheel classifier is a promise about what was verified. This is what makes it one.
    """
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    classifiers = {
        classifier.rsplit(" ", 1)[1]
        for classifier in project["classifiers"]
        if classifier.startswith("Programming Language :: Python :: 3.")
    }
    assert classifiers == set(SUPPORTED_PYTHON_VERSIONS)

    # The floor must be the oldest supported version, not an older one nobody runs.
    assert project["requires-python"] == f">={min(SUPPORTED_PYTHON_VERSIONS)}"

    tested = _matrix_versions("CI.yaml", r'python-version:\s*"(3\.\d+)"')
    assert tested == set(SUPPORTED_PYTHON_VERSIONS), (
        f"the test matrix runs {sorted(tested)} against a published "
        f"{sorted(SUPPORTED_PYTHON_VERSIONS)}"
    )

    built = _matrix_versions(
        "build_and_upload_conda_packages.yaml", r'"(3\.\d+)"'
    )
    assert built == set(SUPPORTED_PYTHON_VERSIONS), (
        f"conda publishes {sorted(built)} against a tested "
        f"{sorted(SUPPORTED_PYTHON_VERSIONS)}"
    )


def test_every_supported_version_is_tested_on_both_operating_systems():
    """A matrix that publishes a version is not the same as one that exercises it.

    Pinned separately because the counts can agree while a cell is missing: dropping one
    macOS row leaves the set of versions unchanged.
    """
    text = (ROOT / ".github" / "workflows" / "CI.yaml").read_text(encoding="utf-8")
    cells = set(re.findall(r'os:\s*(\S+?),\s*python-version:\s*"(3\.\d+)"', text))

    expected = {
        (operating_system, version)
        for operating_system in ("ubuntu-latest", "macos-latest")
        for version in SUPPORTED_PYTHON_VERSIONS
    }

    assert cells == expected, f"missing cells: {sorted(expected - cells)}"


def test_the_recommended_version_is_the_one_the_single_version_jobs_use():
    """One cell of the matrix does the work nobody repeats, and the docs are built once.

    Which version those land on is a statement about what we recommend, so it should not
    be left wherever it happened to be when the matrix last changed. The API resolver, the
    JS suite and the coverage upload run on one cell; the documentation is rendered by one
    environment.
    """
    assert RECOMMENDED_PYTHON_VERSION == max(SUPPORTED_PYTHON_VERSIONS)

    ci = (ROOT / ".github" / "workflows" / "CI.yaml").read_text(encoding="utf-8")
    gated = set(re.findall(r"matrix\.cfg\.python-version == '(3\.\d+)'", ci))
    assert gated == {RECOMMENDED_PYTHON_VERSION}, (
        f"single-cell CI steps run on {sorted(gated)}, not the recommended version"
    )

    for path in ("devtools/conda-envs/development_env.yaml",
                 "devtools/conda-envs/docs_env.yaml",
                 ".github/workflows/sphinx_docs_to_gh_pages.yaml"):
        text = (ROOT / path).read_text(encoding="utf-8")
        found = set(re.findall(r"python=(3\.\d+)", text))
        assert found == {RECOMMENDED_PYTHON_VERSION}, f"{path} pins {sorted(found)}"


def test_the_readme_badge_says_what_we_support():
    """The badge is the first compatibility claim anyone reads, and nothing checked it.

    It said 3.10 | 3.11 | 3.12 — a version we never tested, and missing the one we
    recommend.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"badge/Python-(3\.\d+(?:%20%7C%20\d+\.\d+)*)-blue", readme)

    assert match is not None, "the README has no Python badge"
    advertised = tuple(match.group(1).replace("%20%7C%20", " ").split())

    assert advertised == SUPPORTED_PYTHON_VERSIONS


def test_ruff_targets_the_floor_rather_than_the_recommendation():
    """`target-version` tells ruff which syntax it may assume, so it is the minimum.

    It was `py312` against a floor of 3.11 — which lets ruff rewrite code into something
    the oldest supported interpreter cannot parse. This is the one setting in the repo
    that must *not* follow the recommended version.
    """
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    target = pyproject["tool"]["ruff"]["target-version"]

    assert target == "py" + min(SUPPORTED_PYTHON_VERSIONS).replace(".", "")
