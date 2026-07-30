import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS_ROOT = ROOT / "molsysviewer" / "js"
E2E_ROOT = JS_ROOT / "tests" / "e2e"


def test_default_e2e_command_runs_the_complete_suite():
    package = json.loads((JS_ROOT / "package.json").read_text())

    assert package["scripts"]["test:e2e"] == "npm run test:e2e:all"
    assert package["scripts"]["test:e2e:one"] == "npm run test:e2e:region-hide"
    assert "e2e-runner.js" in package["scripts"]["test:e2e:all"]


def test_e2e_runner_inventory_matches_every_scientific_suite():
    suite_paths = sorted(E2E_ROOT.glob("*.e2e.ts"))
    expected = {path.name.removesuffix(".e2e.ts") for path in suite_paths}
    runner = (E2E_ROOT / "e2e-runner.ts").read_text()
    suite_block = runner.split("const SUITES = [", 1)[1].split("] as const;", 1)[0]
    declared = set(re.findall(r'"([^"]+)"', suite_block))

    # Hardcoded on purpose: adding an E2E file without registering it in the
    # runner (or vice versa) must be a deliberate, visible change.
    assert len(expected) == 25
    assert declared == expected


def test_e2e_suites_use_the_shared_browser_without_silent_success_paths():
    forbidden = (
        "process.exit(0)",
        "data-model scenarios passed",
        "skipping test",
        "skipping Selection subpanel assertions",
    )

    for path in E2E_ROOT.glob("*.e2e.ts"):
        source = path.read_text()
        assert 'from "./e2e-browser"' in source, path.name
        for marker in forbidden:
            assert marker not in source, f"{path.name} contains {marker!r}"


def test_e2e_skip_is_centralized_and_requires_explicit_opt_in():
    source = (E2E_ROOT / "e2e-browser.ts").read_text()

    assert 'process.env.E2E_ALLOW_SKIP === "1"' in source
    assert source.count("process.exit(0)") == 1
    assert "WebGL2 is unavailable" in source
    assert "Chromium launch failed" in source
