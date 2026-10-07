"""Owned HTML storage for isolated Qt probes (uibcdf/molsysviewer#178).

The child receives one HTML path in sys.argv[1], writes it and keeps using it
through its asynchronous reads. The parent removes its private directory only
after subprocess.run returns or terminates/reaps a timed-out child. Caller
outputs/environment remain caller-owned; removal errors propagate. This helper
is test infrastructure, outside the installed viewer API.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def run_qt_html_probe(script: str, *, env: dict[str, str], timeout: float = 90) -> subprocess.CompletedProcess[str]:
    """Capture a real child probe while owning its disposable HTML directory."""
    with tempfile.TemporaryDirectory(prefix="molsysviewer-qt-probe-") as directory:
        path = Path(directory) / "probe.html"
        return subprocess.run(
            [sys.executable, "-c", script, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
