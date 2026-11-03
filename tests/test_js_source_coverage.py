"""Exercise the real c8/esbuild boundary and reject misleading source reports (#290)."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "molsysviewer/js"
NODE = shutil.which("node")
CHECK = JS / "scripts/check-source-coverage.mjs"


def _run(*arguments):
    assert NODE is not None, "Node is required for the JS tooling guards"
    return subprocess.run([NODE, *map(str, arguments)], cwd=JS, capture_output=True, text=True, timeout=90)


@pytest.fixture(scope="module")
def reports(tmp_path_factory):
    """Measure an actual production function, with and without its source map."""
    directory = tmp_path_factory.mktemp("js-coverage")
    probe = directory / "probe.ts"
    source = JS / "src/ui/local-ui-model.ts"
    probe.write_text(
        'import assert from "node:assert/strict";\n'
        'import test from "node:test";\n'
        f"import {{ createLocalUiModel }} from {json.dumps(source.as_posix())};\n"
        'test("measure the real UI model", () => {\n'
        '  const model = createLocalUiModel({ viewer_mode: "integrated" });\n'
        '  assert.equal(model.get("viewer_mode"), "standard");\n'
        '  model.set("viewer_mode", "cinema");\n'
        '  assert.equal(model.get("viewer_mode"), "cinema");\n'
        "});\n",
        encoding="utf-8",
    )
    for name in ("mapped", "unmapped"):
        bundle = directory / f"{name}.mjs"
        built = _run(
            "--input-type=module",
            "-e",
            "import {buildSync} from 'esbuild'; buildSync({entryPoints:[process.argv[1]],"
            "bundle:true,platform:'node',format:'esm',outfile:process.argv[2],"
            "sourcemap:process.argv[3]==='mapped'});",
            probe,
            bundle,
            name,
        )
        assert built.returncode == 0, built.stderr
        report = directory / name
        measured = _run(
            JS / "node_modules/c8/bin/c8.js",
            "--config=.c8rc.json",
            f"--reports-dir={report}",
            "node",
            "--test",
            "--test-reporter=tap",
            bundle,
        )
        assert measured.returncode == 0, measured.stdout + measured.stderr
        assert "# pass 1" in measured.stdout, measured.stdout
        assert "measure the real UI model" in measured.stdout, measured.stdout
    return directory


def test_real_production_functions_are_covered_and_unmapped_runner_is_rejected(reports):
    mapped = _run(CHECK, reports / "mapped")
    assert mapped.returncode == 0, mapped.stderr
    assert "1 files" in mapped.stdout
    summary = json.loads((reports / "mapped/coverage-summary.json").read_text())
    source = str(JS / "src/ui/local-ui-model.ts")
    assert summary[source]["functions"]["covered"] > 0
    # The uncalled on/off methods are not silently reported as executed.
    assert summary[source]["functions"]["covered"] < summary[source]["functions"]["total"]
    unmapped = _run(CHECK, reports / "unmapped")
    assert unmapped.returncode != 0, unmapped.stdout
    assert "no production source records" in unmapped.stderr


@pytest.mark.parametrize("defect", ["missing", "empty", "harness", "false-full", "missing-lines"])
def test_report_gate_rejects_broken_or_nonproduction_coverage(reports, tmp_path, defect):
    # Start with measured bytes, then damage one boundary. These are negative
    # controls, never evidence claimed as generated production coverage.
    directory = tmp_path / "report"
    shutil.copytree(reports / "mapped", directory)
    lcov = directory / "lcov.info"
    summary = directory / "coverage-summary.json"
    if defect == "missing":
        lcov.unlink()
    elif defect == "empty":
        lcov.write_text("")
    elif defect == "harness":
        measured = json.loads(summary.read_text())
        original = str(JS / "src/ui/local-ui-model.ts")
        harness = str(JS / "tests/unit/local-ui-model.test.ts")
        measured[harness] = measured.pop(original)
        summary.write_text(json.dumps(measured))
        lcov.write_text(lcov.read_text().replace("src/ui/local-ui-model.ts", "tests/unit/local-ui-model.test.ts"))
    elif defect == "false-full":
        measured = json.loads(summary.read_text())
        for counters in measured.values():
            counters["functions"].update(total=0, covered=0, pct=100)
        summary.write_text(json.dumps(measured))
        lcov.write_text(re.sub(r"^(FNF|FNH):\d+", r"\1:0", lcov.read_text(), flags=re.MULTILINE))
    else:
        lcov.write_text("\n".join(line for line in lcov.read_text().splitlines() if not line.startswith("DA:")))
    rejected = _run(CHECK, directory)
    assert rejected.returncode != 0, rejected.stdout
    assert "Invalid JavaScript source coverage" in rejected.stderr


def test_unit_coverage_is_required_before_python_and_upload():
    scripts = json.loads((JS / "package.json").read_text())["scripts"]
    assert "--sourcemap" in scripts["build:test:js"]
    assert "tests/unit/index.test.ts" in scripts["build:test:js"]
    assert scripts["coverage:js"] == (
        "npm run build:test:js && c8 --config=.c8rc.json node --test tests/unit/dist-index.js"
        " && node scripts/check-source-coverage.mjs"
    )
    workflow = yaml.safe_load((ROOT / ".github/workflows/CI.yaml").read_text())
    steps = workflow["jobs"]["test"]["steps"]
    unit = next(i for i, step in enumerate(steps) if step.get("name") == "JS unit tests (Node)")
    python = next(i for i, step in enumerate(steps) if step.get("name") == "Run tests")
    upload = next(i for i, step in enumerate(steps) if step.get("name") == "Upload coverage reports to Codecov")
    assert unit < python < upload
    assert steps[unit]["run"].strip() == "npm run coverage:js"
    assert not steps[unit].get("continue-on-error")
