"""Where the JS build gets its version when there is no `_version.py`.

Three callers build the runtime before any Python exists: the npm release workflow, which
has only the tag; `devtools/conda-build/build.sh`, which exports `RELEASE_VERSION` from
`PKG_VERSION` and builds the bundle before `pip install`; and `CI_e2e`. `build-runtime.mjs`
read `_version.py` directly and threw `ENOENT`, so 0.20.1, 0.22.0 and 0.23.0 never reached
npm and the next conda build would have failed the same way (uibcdf/molsysviewer#88).

These tests run the real scripts against a miniature source tree, so they exercise the
resolution and the injection without rebuilding the 6 MB bundle.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "molsysviewer" / "js"
NODE = shutil.which("node")


def _miniature_checkout(tmp_path: Path) -> Path:
    """A tree shaped like the repository, with one trivial module instead of the runtime."""
    js = tmp_path / "molsysviewer" / "js"
    (js / "src").mkdir(parents=True)
    shutil.copytree(JS / "scripts", js / "scripts")
    (js / "node_modules").symlink_to(JS / "node_modules")
    (js / "src" / "index.ts").write_text("export const version: string = __MOLSYSVIEWER_VERSION__;\n", encoding="utf-8")
    (js / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2019"}}), encoding="utf-8")
    (js / "package.json").write_text(
        json.dumps({"name": "@uibcdf/molsysviewer", "version": "0.0.1", "type": "module"}) + "\n",
        encoding="utf-8",
    )
    return js


def _build(js: Path, **environment: str) -> str:
    assert NODE is not None, "node is required to build the runtime and is not on PATH"
    completed = subprocess.run(
        [NODE, str(js / "scripts" / "build-runtime.mjs")],
        cwd=js,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    return (js.parent / "viewer.js").read_text(encoding="utf-8")


def test_the_runtime_takes_its_version_from_the_release_when_there_is_no_version_file(tmp_path):
    """The exact failure that stopped three releases: no `_version.py`, a tag in hand."""
    js = _miniature_checkout(tmp_path)

    bundle = _build(js, RELEASE_VERSION="9.8.7")

    assert '"9.8.7"' in bundle, "the runtime did not take the release version it was given"


def test_the_version_file_outranks_the_environment(tmp_path):
    """A development build reports what it was built from, whatever the environment says.

    Without this order, a stale `RELEASE_VERSION` left in a shell would silently stamp a
    developer's runtime with a version that is not the code in it.
    """
    js = _miniature_checkout(tmp_path)
    (js.parent / "_version.py").write_text('__version__ = "1.2.3+4.gabcdef"\n', encoding="utf-8")

    bundle = _build(js, RELEASE_VERSION="9.8.7")

    assert '"1.2.3+4.gabcdef"' in bundle
    assert "9.8.7" not in bundle


def test_the_npm_manifest_takes_the_release_version_too(tmp_path):
    """`npm run build` is sync-then-build, and the two must resolve the same way.

    They did not: the sync step had the environment fallback and the build step did not.
    """
    js = _miniature_checkout(tmp_path)

    completed = subprocess.run(
        [NODE, str(js / "scripts" / "sync-python-version.mjs")],
        cwd=js,
        env={**os.environ, "RELEASE_VERSION": "9.8.7"},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((js / "package.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "9.8.7"
    assert manifest["pythonVersion"] == "9.8.7"


def test_no_build_script_reads_the_version_file_on_its_own():
    """The defect was one script resolving the version its own way. Two did; now neither does.

    Structural, because the behaviour above cannot see a third script added later.
    """
    offenders = []
    for script in sorted((JS / "scripts").glob("*.mjs")):
        if script.name == "resolve-version.mjs":
            continue
        text = script.read_text(encoding="utf-8")
        if "__version__" in text and "resolveBuildVersion" not in text:
            offenders.append(script.name)

    assert offenders == [], (
        f"these build scripts parse _version.py themselves instead of using the shared "
        f"resolver, which is how the npm and conda publishers diverged: {offenders}"
    )
