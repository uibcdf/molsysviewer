"""A successful esbuild bundle alone cannot guard cross-class private access."""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_ROOT = ROOT / "molsysviewer/js"


def test_runtime_sources_pass_real_typescript_access_checks():
    node = shutil.which("node")
    compiler = JS_ROOT / "node_modules/typescript/bin/tsc"
    assert node is not None, "The core source suite requires Node from the test environment."
    assert compiler.is_file(), "Run npm ci before the core source suite."
    completed = subprocess.run(
        [node, str(compiler), "--noEmit"], cwd=JS_ROOT, capture_output=True, text=True, timeout=120
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
