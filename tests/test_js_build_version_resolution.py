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

import pytest

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


@pytest.mark.parametrize("target", ["runtime", "unit", "harness"])
@pytest.mark.parametrize("unreviewed", ["version", "bytes"])
def test_build_routes_refuse_unreviewed_molstar_cache_inputs(tmp_path, target, unreviewed):
    """Every actual build route must reject an unqualified provider repair."""
    assert NODE is not None
    js = _miniature_checkout(tmp_path)
    (js / "node_modules").unlink()
    (js / "node_modules").mkdir()
    (js / "node_modules" / "esbuild").symlink_to(JS / "node_modules" / "esbuild")
    provider = js / "node_modules" / "molstar"
    provider.mkdir()
    metadata = json.loads((JS / "node_modules" / "molstar" / "package.json").read_text(encoding="utf-8"))
    if unreviewed == "version":
        metadata["version"] = "99.0.0"
    (provider / "package.json").write_text(json.dumps(metadata), encoding="utf-8")
    # Keep the independent image-readiness boundary qualified so this fault
    # still reaches the component-cache bytes it is meant to exercise.
    assets = json.loads((JS / "scripts/reviewed-image-assets.json").read_text(encoding="utf-8"))
    for name in assets["files"]:
        target_file = provider / name
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(JS / "node_modules/molstar" / name, target_file)
    relative = Path("lib/mol-model-formats/structure/basic/properties.js")
    source = provider / relative
    source.parent.mkdir(parents=True)
    native = (JS / "node_modules" / "molstar" / relative).read_text(encoding="utf-8")
    source.write_text(
        native + "\n// Unreviewed provider bytes.\n" if unreviewed == "bytes" else native, encoding="utf-8"
    )

    entry = {
        "runtime": "src/index.ts",
        "unit": "tests/unit/index.test.ts",
        "harness": "tests/e2e/harness.ts",
    }[target]
    (js / entry).parent.mkdir(parents=True, exist_ok=True)
    (js / entry).write_text(
        'export { getChemicalComponentMap } from "molstar/lib/mol-model-formats/structure/basic/properties";\n',
        encoding="utf-8",
    )
    command = [NODE, str(js / "scripts" / "build-runtime.mjs")]
    if target != "runtime":
        command = [NODE, str(js / "scripts" / "build-test-bundles.mjs"), target]
    result = subprocess.run(command, cwd=js, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    expected = "component-cache compatibility before building" if unreviewed == "version" else "reviewed bytes"
    assert expected in result.stderr
    assert not (js.parent / "viewer.js").exists()
    assert not (js / "tests/unit/dist-index.js").exists()
    assert not (js / "tests/e2e/harness.bundle.js").exists()


@pytest.mark.parametrize("target", ["runtime", "unit", "harness"])
def test_build_routes_keep_installed_molstar_when_a_source_checkout_exists(tmp_path, target):
    """A leftover inspection checkout cannot override the locked native source."""
    assert NODE is not None
    js = _miniature_checkout(tmp_path)
    shutil.copyfile(JS / "tsconfig.json", js / "tsconfig.json")
    entry = {
        "runtime": "src/index.ts",
        "unit": "tests/unit/index.test.ts",
        "harness": "tests/e2e/harness.ts",
    }[target]
    (js / entry).parent.mkdir(parents=True, exist_ok=True)
    (js / entry).write_text(
        'export { getChemicalComponentMap } from "molstar/lib/mol-model-formats/structure/basic/properties";\n',
        encoding="utf-8",
    )
    # Deliberate source-origin fault input. The real installed Mol* and its
    # byte-reviewed repair remain untouched, rather than replacing their code.
    shadow = js.parent / "src_molstar/src/mol-model-formats/structure/basic/properties.ts"
    shadow.parent.mkdir(parents=True)
    shadow.write_text(
        'export const getChemicalComponentMap = "UNQUALIFIED_SIBLING_SOURCE_SELECTED";\n', encoding="utf-8"
    )
    command = [NODE, str(js / "scripts" / "build-runtime.mjs")]
    if target != "runtime":
        command = [NODE, str(js / "scripts" / "build-test-bundles.mjs"), target]
    result = subprocess.run(command, cwd=js, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    output = {
        "runtime": js.parent / "viewer.js",
        "unit": js / "tests/unit/dist-index.js",
        "harness": js / "tests/e2e/harness.bundle.js",
    }[target]
    bundle = output.read_text(encoding="utf-8")
    assert "UNQUALIFIED_SIBLING_SOURCE_SELECTED" not in bundle
    assert "uniqueComponentNamesCache" in bundle, "the native cache repair was bypassed"


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


def test_the_typescript_project_checks_without_library_overrides():
    """The actual project config must admit the standard APIs its source uses."""
    assert NODE is not None
    compiler = JS / "node_modules/typescript/bin/tsc"
    assert compiler.is_file(), "the declared TypeScript development dependency is required"
    result = subprocess.run(
        [NODE, str(compiler), "--noEmit", "--project", str(JS / "tsconfig.json")],
        cwd=JS,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


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
