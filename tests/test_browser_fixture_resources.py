"""Execute the browser fixture owner with real Node/filesystem resources."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("fail", [False, True])
def test_fixture_owner_cleans_success_and_failure_without_deleting_caller_output(tmp_path, fail):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node required for the browser tooling lifecycle guard")
    helper = Path(__file__).parents[1] / "molsysviewer/js/tests/e2e/fixture-workspace.ts"
    caller = tmp_path / "keep.txt"
    caller.write_text("retained evidence")
    script = f"""
import {{ withFixtureWorkspace, fixtureEnvironment }} from {json.dumps(helper.as_uri())};
import assert from "node:assert/strict";
import {{ writeFile, mkdir }} from "node:fs/promises";
let owned;
try {{
    const value = await withFixtureWorkspace("guard", async directory => {{
        owned = directory;
        const env = fixtureEnvironment(directory);
        assert.equal(env.TMPDIR, directory);
        assert.equal(env.TMP, directory);
        assert.equal(env.TEMP, directory);
        await mkdir(directory + "/child");
        await writeFile(directory + "/child/export.html", "temporary fixture");
        if ({str(fail).lower()}) throw new Error("rejected operation");
        return 17;
    }});
    assert.equal(value, 17);
}} catch (error) {{
    assert.equal({str(fail).lower()}, true);
    assert.equal(error.message, "rejected operation");
}}
console.log(JSON.stringify({{ owned }}));
"""
    result = subprocess.run(
        [node, "--experimental-strip-types", "--input-type=module", "-e", script],
        env={**os.environ, "TMPDIR": str(tmp_path), "TMP": str(tmp_path), "TEMP": str(tmp_path)},
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    workspace = Path(json.loads(result.stdout)["owned"])
    assert workspace.parent == tmp_path
    assert not workspace.exists()
    assert caller.read_text() == "retained evidence"
