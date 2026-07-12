from pathlib import Path
import json
import subprocess
import sys


SCRIPT = Path(__file__).parents[1] / "scripts" / "api_resolver.py"


def _run_resolver(corpus: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(corpus)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_api_resolver_accepts_live_view_api(tmp_path):
    (tmp_path / "valid.md").write_text(
        "```python\nview.regions.tags()\nviewer.MolSysView()\n```\n",
        encoding="utf-8",
    )

    result = _run_resolver(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 unresolved" in result.stdout


def test_api_resolver_rejects_dead_view_api(tmp_path):
    (tmp_path / "invalid.py").write_text(
        "view.player.set_frame_range(0, 10)\n",
        encoding="utf-8",
    )

    result = _run_resolver(tmp_path)

    assert result.returncode == 1
    assert "view.player.set_frame_range" in result.stdout


def test_api_resolver_checks_notebook_cells_with_ipython_magics(tmp_path):
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["%matplotlib inline\n", "view.player.missing_method()\n"],
            }
        ]
    }
    (tmp_path / "invalid.ipynb").write_text(json.dumps(notebook), encoding="utf-8")

    result = _run_resolver(tmp_path)

    assert result.returncode == 1
    assert "view.player.missing_method" in result.stdout
