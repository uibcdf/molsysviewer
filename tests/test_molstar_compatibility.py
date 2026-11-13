"""Actual native chemistry and lifetime controls for the bounded Mol* build seam."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "molsysviewer/js"


@pytest.mark.parametrize("fault", ["none", "digest", "missing"])
def test_image_assets_build_guard_rejects_changed_native_bytes(tmp_path, fault):
    """The private readiness reader cannot silently consume changed native code."""
    node = shutil.which("node")
    assert node is not None
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    native = tmp_path / "node_modules/molstar"
    native.mkdir(parents=True)
    qualified = JS / "scripts/reviewed-image-assets.json"
    manifest = json.loads(qualified.read_text())
    assert manifest["version"] == json.loads((JS / "node_modules/molstar/package.json").read_text())["version"]
    assert set(manifest["files"]) == {
        "lib/mol-canvas3d/passes/image.js",
        "lib/mol-canvas3d/passes/draw.js",
        "lib/mol-canvas3d/passes/postprocessing.js",
        "lib/mol-canvas3d/passes/smaa.js",
        "lib/mol-gl/webgl/texture.js",
    }
    for name, digest in manifest["files"].items():
        source = JS / "node_modules/molstar" / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        target = native / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copy2(JS / "node_modules/molstar/package.json", native / "package.json")
    shutil.copy2(JS / "scripts/molstar-component-cache.mjs", scripts)
    shutil.copy2(qualified, scripts)
    victim = native / "lib/mol-canvas3d/passes/smaa.js"
    if fault == "digest":
        victim.write_text(victim.read_text() + "\n// Unreviewed native modification.\n")
    elif fault == "missing":
        victim.unlink()
    entry = tmp_path / "entry.js"
    entry.write_text("export const control = 1;\n")
    output = tmp_path / "output.js"
    builder = tmp_path / "build.mjs"
    builder.write_text(
        f"import {{ build }} from {json.dumps((JS / 'node_modules/esbuild/lib/main.js').as_uri())};\n"
        f"import {{ molstarComponentCachePlugin }} from {json.dumps((scripts / 'molstar-component-cache.mjs').as_uri())};\n"
        f"await build({{ entryPoints: [{json.dumps(str(entry))}], outfile: {json.dumps(str(output))}, "
        "bundle: true, plugins: [molstarComponentCachePlugin()] });\n"
    )
    result = subprocess.run([node, str(builder)], capture_output=True, text=True, timeout=30)
    if fault == "none":
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.is_file()
    else:
        assert result.returncode != 0
        assert not output.exists(), "An unqualified readiness seam must emit no bundle."
        if fault == "digest":
            assert "image-asset source differs" in result.stderr


def test_component_cache_repair_preserves_native_chemistry_and_releases_inputs(tmp_path):
    """Only the weak cache releases tables/buffers; both native readers agree."""
    node = shutil.which("node")
    assert node is not None
    builder = tmp_path / "build.mjs"
    builder.write_text(
        f"import {{ build }} from {json.dumps((JS / 'node_modules/esbuild/lib/main.js').as_uri())};\n"
        f"import {{ molstarComponentCachePlugin }} from "
        f"{json.dumps((JS / 'scripts/molstar-component-cache.mjs').as_uri())};\n"
        'import { writeFile } from "node:fs/promises";\n'
        "const adapted = process.argv[2] === 'adapted';\n"
        "const result = await build({ entryPoints: [process.argv[3]], outfile: process.argv[4],\n"
        '  absWorkingDir: process.argv[5], nodePaths: [process.argv[5] + "/node_modules"],\n'
        '  bundle: true, platform: "node", format: "esm", metafile: true,\n'
        "  plugins: adapted ? [molstarComponentCachePlugin()] : [] });\n"
        'await writeFile(process.argv[4] + ".inputs.json", JSON.stringify(result.metafile.inputs));\n',
        encoding="utf-8",
    )
    results = {}
    for variant in ["native", "adapted"]:
        output = tmp_path / f"{variant}.mjs"
        build = subprocess.run(
            [node, str(builder), variant, str(JS / "tests/fixtures/molstar-component-cache.mjs"), str(output), str(JS)],
            cwd=JS,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert build.returncode == 0, build.stdout + build.stderr
        inputs = json.loads(Path(str(output) + ".inputs.json").read_text())
        native_inputs = [(JS / name).resolve() for name in inputs if "molstar/" in name]
        assert native_inputs, "The native control must actually include Mol*."
        assert all(path.is_relative_to(JS / "node_modules/molstar") for path in native_inputs)
        observed = subprocess.run(
            [node, "--expose-gc", str(output)],
            cwd=JS,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert observed.returncode == 0, observed.stdout + observed.stderr
        results[variant] = json.loads(observed.stdout)

    assert results["adapted"]["summaries"] == results["native"]["summaries"]
    assert results["native"]["retained"] == [{"data": True, "table": True, "buffer": True}] * 5
    assert results["adapted"]["retained"] == [{"data": False, "table": False, "buffer": False}] * 5


def test_native_probe_alias_overrides_an_unqualified_ancestor(tmp_path):
    """An out-of-package entry must consume the explicitly requested real Mol*."""
    node = shutil.which("node")
    assert node is not None
    provider = JS / "node_modules/molstar"
    version = json.loads((provider / "package.json").read_text())["version"]
    foreign = tmp_path / "node_modules/molstar"
    foreign.mkdir(parents=True)
    (foreign / "package.json").write_text(json.dumps({"name": "molstar", "version": "99.0.0"}))
    fault = foreign / "lib/mol-model-formats/structure/basic/properties.js"
    fault.parent.mkdir(parents=True)
    fault.write_text('throw new Error("UNQUALIFIED_NATIVE_SELECTED");\n')
    entry = tmp_path / "probe.mjs"
    entry.write_text(
        'import { getChemicalComponentMap } from "molstar/lib/mol-model-formats/structure/basic/properties";\n'
        "console.log(typeof getChemicalComponentMap);\n"
    )
    output = tmp_path / "qualified.cjs"
    built = subprocess.run(
        [node, str(JS / "scripts/build-molstar-probe.mjs"), str(entry), str(provider), str(output), version],
        cwd=JS,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    evidence = json.loads(Path(str(output) + ".inputs.json").read_text())
    assert evidence["provider"]["root"] == str(provider.resolve())
    assert evidence["provider"]["version"] == version
    assert evidence["native_inputs"]
    for name, digest in evidence["native_inputs"].items():
        path = Path(name)
        assert path.is_relative_to(provider.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    observed = subprocess.run([node, str(output)], capture_output=True, text=True, timeout=30)
    assert observed.returncode == 0, observed.stdout + observed.stderr
    assert observed.stdout.strip() == "function"


@pytest.mark.parametrize("fault", ["version", "origin"])
def test_native_probe_refuses_unqualified_inputs_before_emitting(tmp_path, fault):
    """Identity faults fail closed and leave no supposedly qualified executable."""
    node = shutil.which("node")
    assert node is not None
    provider = JS / "node_modules/molstar"
    version = json.loads((provider / "package.json").read_text())["version"]
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "package.json").write_text(json.dumps({"name": "molstar", "version": "99.0.0"}))
    module = foreign / "foreign.js"
    module.write_text('export const fault = "foreign provider";\n')
    entry = tmp_path / "probe.mjs"
    entry.write_text(
        'export { getChemicalComponentMap } from "molstar/lib/mol-model-formats/structure/basic/properties";\n'
        + (f"export {{ fault }} from {json.dumps(str(module))};\n" if fault == "origin" else "")
    )
    output = tmp_path / "rejected.cjs"
    built = subprocess.run(
        [
            node,
            str(JS / "scripts/build-molstar-probe.mjs"),
            str(entry),
            str(provider),
            str(output),
            "99.0.0" if fault == "version" else version,
        ],
        cwd=JS,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert built.returncode != 0
    expected = "requires molstar" if fault == "version" else "different Mol* origin"
    assert expected in built.stderr
    assert not output.exists()
    assert not Path(str(output) + ".inputs.json").exists()
