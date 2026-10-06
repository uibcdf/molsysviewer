"""Exercise the real read-only audit against mutated repository metadata."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "devtools/audit_dependency_contract.py"


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "viewer"
    paths = [
        ROOT / "pyproject.toml",
        ROOT / "devtools/dependency_contract.toml",
        ROOT / "devtools/conda-build/meta.yaml",
    ]
    paths += list((ROOT / "devtools/conda-envs").glob("*.yaml"))
    paths += list((ROOT / ".github/workflows").glob("*.y*ml"))
    for path in paths:
        target = root / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return root


def _run(root, *args, env=None):
    inputs = [root / "pyproject.toml", root / "devtools/dependency_contract.toml"]
    inputs += list((root / "devtools").rglob("*.yaml"))
    inputs += list((root / ".github/workflows").glob("*.y*ml"))
    before = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs if path.is_file()
    }
    result = subprocess.run(
        [sys.executable, str(AUDITOR), "--root", str(root), *args], capture_output=True, text=True, env=env, timeout=60
    )
    after = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs if path.is_file()
    }
    assert before == after, "the dependency audit changed the input tree"
    return result


def _replace(root, path, old, new):
    target = root / path
    text = target.read_text(encoding="utf-8")
    assert old in text
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_current_repository_contract_passes_without_importing_the_viewer():
    result = _run(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "API compatibility remains a separate gate" in result.stdout


@pytest.mark.parametrize("flavour,base", [(PurePosixPath, "/checkout"), (PureWindowsPath, "D:/checkout")])
@pytest.mark.parametrize(
    "relative",
    [
        "devtools/conda-build/meta.yaml",
        "devtools/conda-envs/test_source_pair_py314.yaml",
        ".github/workflows/ci-python-314-source-pair.yaml",
    ],
)
def test_dependency_inventory_paths_use_portable_separators(flavour, base, relative):
    serializer = runpy.run_path(str(AUDITOR))["_inventory_path"]
    root = flavour(base)
    assert serializer(root, root / relative) == relative


def test_repository_argument_on_an_evidence_action_is_not_a_source_checkout(tree):
    (tree / ".github/workflows/evidence.yaml").write_text(
        "jobs:\n  verify:\n    steps:\n"
        "      - uses: uibcdf/molsyssuite/.github/actions/verify-installed-matrix@" + "a" * 40 + "\n"
        "        with:\n          repository: uibcdf/molsysmt\n",
        encoding="utf-8",
    )
    result = _run(tree)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("fault", ["unclassified", "duplicate"])
def test_real_undeclared_or_duplicate_source_checkouts_remain_rejected(tree, fault):
    path = tree / ".github/workflows/ci-python-314-source-pair.yaml"
    data = yaml.safe_load(path.read_text())
    steps = data["jobs"]["source-pair"]["steps"]
    checkout = next(step for step in steps if step.get("with", {}).get("repository") == "uibcdf/molsysmt")
    if fault == "duplicate":
        steps.append(checkout.copy())
        path.write_text(yaml.safe_dump(data))
    else:
        path = tree / ".github/workflows/undeclared-source.yaml"
        path.write_text(yaml.safe_dump({"jobs": {"consumer": {"steps": [checkout]}}}))
    result = _run(tree)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "unclassified or duplicate source checkout uibcdf/molsysmt" in result.stdout


@pytest.mark.parametrize(
    "path,old,new,diagnostic",
    [
        ("devtools/conda-build/meta.yaml", "argdigest >=0.13.0", "argdigest >=0.12.0", "violates"),
        ("devtools/conda-build/meta.yaml", "smonitor >=0.13.0", "smonitor", "violates"),
        ("devtools/conda-build/meta.yaml", "python >=3.11,<3.15", "python >=3.11", "host Python"),
        ("devtools/conda-build/meta.yaml", "argdigest >=0.13.0", "argdigest >=0.14.0", "violates"),
        ("devtools/conda-envs/test_env.yaml", "  - smonitor>=0.13.0\n", "", "missing smonitor"),
        ("devtools/conda-envs/docs_env.yaml", "pyunitwizard>=0.25.0", "pyunitwizard>=0.24.0", "violates"),
        ("devtools/conda-envs/development_env.yaml", "python=3.13", "python=3.15", "violates python"),
        ("devtools/conda-envs/test_env.yaml", "python>=3.11,<3.15", "python>=3.11,<3.16", "violates python"),
        ("devtools/conda-envs/test_env.yaml", "argdigest>=0.13.0", "argdigest", "violates"),
        ("devtools/conda-envs/test_env.yaml", "  - numpy\n", "  - numpy\n  - numpy\n", "duplicate"),
        (
            "devtools/conda-envs/test_env.yaml",
            "argdigest>=0.13.0",
            "argdigest>=0.13.0; python_version<'3.14'",
            "unsupported",
        ),
        ("devtools/dependency_contract.toml", "schema = 1", "schema = 7", "schema"),
        (
            "devtools/dependency_contract.toml",
            'source_supplied = ["molsysmt"]',
            'source_supplied = ["smonitor"]',
            "source",
        ),
        (
            "devtools/dependency_contract.toml",
            'runtime_tools = ["packaging"]',
            "runtime_tools = []",
            "excluded environment",
        ),
        (
            ".github/workflows/ci-python-314-source-pair.yaml",
            "ref: ${{ inputs.molsysmt_sha || '46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9' }}",
            "ref: main",
            "exact SHA",
        ),
        (
            ".github/workflows/ci-python-314-source-pair.yaml",
            '--installed-source "molsysmt=../molsysmt-source@$MOLSYSMT_SHA"',
            "--installed-source ignored",
            "missing installed-source",
        ),
        (
            ".github/workflows/ci-python-314-source-pair.yaml",
            "      - name: Audit dependency routes",
            "      - if: false\n        name: Audit dependency routes",
            "missing installed-source",
        ),
    ],
)
def test_rejects_dependency_and_route_drift(tree, path, old, new, diagnostic):
    _replace(tree, path, old, new)
    result = _run(tree)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout


def test_new_environment_requires_classification(tree):
    (tree / "devtools/conda-envs/new.yaml").write_text("dependencies: [python=3.13]\n", encoding="utf-8")
    result = _run(tree)
    assert result.returncode == 1
    assert "inventory differs" in result.stdout


def test_new_recipe_requires_classification(tree):
    shutil.copy2(tree / "devtools/conda-build/meta.yaml", tree / "devtools/recipe.yaml")
    result = _run(tree)
    assert result.returncode == 1
    assert "recipe inventory differs" in result.stdout


def test_stronger_environment_constraint_is_allowed(tree):
    _replace(tree, "devtools/conda-envs/test_env.yaml", "argdigest>=0.13.0", "argdigest>=0.14.0,<1")
    result = _run(tree)
    assert result.returncode == 0, result.stdout + result.stderr


def _installed_fixture(tree, tmp_path, version="2.0"):
    # Real git checkout and importlib.metadata-readable distribution records; no
    # mocks of the metadata lookup or VCS commands used by the auditor.
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text('[project]\nname="contract-probe"\nversion="2.0"\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", "pyproject.toml"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Contract Test",
            "-c",
            "user.email=contract@example.invalid",
            "commit",
            "-qm",
            "Fixture",
        ],
        check=True,
    )
    sha = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    site = tmp_path / "site"
    dist = site / "contract_probe-2.0.dist-info"
    dist.mkdir(parents=True)
    (dist / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: contract-probe\nVersion: {version}\n", encoding="utf-8"
    )
    (dist / "direct_url.json").write_text(json.dumps({"url": source.as_uri(), "dir_info": {}}), encoding="utf-8")
    _replace(tree, "pyproject.toml", '  "numpy",', '  "numpy",\n  "contract-probe>=2",')
    _replace(tree, "devtools/conda-build/meta.yaml", "    - numpy\n", "    - numpy\n    - contract-probe >=2\n")
    for path in (tree / "devtools/conda-envs").glob("*.yaml"):
        if path.name != "build_env.yaml":
            _replace(tree, str(path.relative_to(tree)), "dependencies:\n", "dependencies:\n  - contract-probe>=2\n")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(site)
    return source, sha, dist, env


@pytest.mark.parametrize("fault", [None, "version", "sha", "dirty", "origin", "missing_origin", "missing_install"])
def test_installed_source_floor_and_identity(tree, tmp_path, fault):
    source, sha, dist, env = _installed_fixture(tree, tmp_path, version="1.9" if fault == "version" else "2.0")
    if fault == "sha":
        sha = "0" * 40
    elif fault == "dirty":
        (source / "pyproject.toml").write_text('[project]\nname="contract-probe"\nversion="2.1"\n', encoding="utf-8")
    elif fault == "origin":
        (dist / "direct_url.json").write_text(json.dumps({"url": tmp_path.as_uri(), "dir_info": {}}), encoding="utf-8")
    elif fault == "missing_origin":
        (dist / "direct_url.json").unlink()
    elif fault == "missing_install":
        shutil.rmtree(dist)
    result = _run(tree, "--installed-source", f"contract-probe={source}@{sha}", env=env)
    assert result.returncode == (0 if fault is None else 1), result.stdout + result.stderr
    if fault is not None:
        assert "contract-probe" in result.stdout


def test_audit_is_wired_before_packaging_and_in_metadata_ci():
    import yaml

    deployment = yaml.safe_load((ROOT / ".github/workflows/build_and_upload_conda_packages.yaml").read_text())
    steps = deployment["jobs"]["conda_deployment_with_new_tag"]["steps"]
    audit = next(i for i, step in enumerate(steps) if "audit_dependency_contract.py" in step.get("run", ""))
    build = next(i for i, step in enumerate(steps) if "python -m build" in step.get("run", ""))
    upload = next(i for i, step in enumerate(steps) if "action-build-and-upload-conda-packages" in step.get("uses", ""))
    assert audit <= build < upload
    run = steps[audit]["run"]
    assert run.index("audit_dependency_contract.py") < run.index("python -m build")
    ci = yaml.safe_load((ROOT / ".github/workflows/molsyssuite-policy.yml").read_text())
    assert any(
        "audit_dependency_contract.py" in step.get("run", "") for step in ci["jobs"]["dependency-contract"]["steps"]
    )
