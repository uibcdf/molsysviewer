"""Run scientific Interactions checks against installed Viewer/provider artifacts.

Invoke with the isolated interpreter's ``-I`` flag from outside the checkouts.
The source root supplies fixture tools and tests; scientific imports must come
from that interpreter's site-packages. Expected versions identify the pair,
without declaring that an experimental provider is a published dependency.
``--tests`` selects pytest nodes relative to ``SOURCE_ROOT/tests`` (or absolute
nodes); ``--pytest-args`` forwards output options. By default, run the five
bounded scientific/projection/persistence modules.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import sys
import sysconfig
from pathlib import Path
from runpy import run_path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTS = (
    "test_interactions_projection_batching.py",
    "test_interaction_families.py",
    "test_interactions_scene.py",
    "test_interactions_qualification.py",
    "test_interactions_residency_benchmark.py",
)


def verify_imports(expected_versions):
    """Check every loaded scientific module, including imports made by fixtures."""
    sites = {Path(sysconfig.get_path(kind)).resolve() for kind in ("purelib", "platlib")}
    for package, expected in expected_versions.items():
        # Pytest/tools can alter discovery order in a system-site-packages venv.
        # Identify the artifact in this interpreter's own installation, while
        # checking every loaded scientific module independently below.
        distributions = list(importlib.metadata.Distribution.discover(name=package, path=list(map(str, sites))))
        if len(distributions) != 1:
            raise ValueError(f"Expected one installed {package} distribution in {sites}, found {len(distributions)}.")
        actual = distributions[0].version
        if actual != expected:
            raise ValueError(f"Expected {package} {expected}, found {actual}.")
        for name, module in tuple(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if filename and (name == package or name.startswith(package + ".")):
                path = Path(filename).resolve()
                if not any(path.is_relative_to(site / package) for site in sites):
                    raise ValueError(f"Installed qualification imported {name} from {path}, outside {sites}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--expected-viewer-version", required=True)
    parser.add_argument("--expected-provider-version", required=True)
    parser.add_argument("--tests", nargs="+", default=DEFAULT_TESTS)
    parser.add_argument("--pytest-args", nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args()
    root = args.source_root.resolve()
    if not (root / "tests/conftest.py").is_file() or not (root / "devtools/interaction_family_fixtures.py").is_file():
        parser.error("The source root must supply the Viewer tests and scientific fixture tools.")

    import molsysmt
    import pytest

    import molsysviewer  # noqa: F401

    expected = {"molsysmt": args.expected_provider_version, "molsysviewer": args.expected_viewer_version}
    verify_imports(expected)
    if not hasattr(molsysmt, "Interactions"):
        raise ValueError("The installed provider has no Interactions API; this pair cannot qualify the feature.")

    # Make only the fixture namespace importable, without prepending a scientific
    # checkout. Subsequent imports are checked again when pytest finishes.
    run_path(str(Path(__file__).with_name("_fixture_namespace.py")))["expose_fixture_namespace"](root)
    os.environ["MOLSYSVIEWER_TEST_INSTALLED"] = "1"
    targets = [name if Path(name).is_absolute() else str(root / "tests" / name) for name in args.tests]
    result = pytest.main(["--import-mode=importlib", *targets, *args.pytest_args])
    verify_imports(expected)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
