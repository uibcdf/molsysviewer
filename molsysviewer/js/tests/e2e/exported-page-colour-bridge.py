"""Produce a real exported page for the colour E2E to embed.

Not a fixture built in TypeScript, for the same reason as
`exported-page-framing-bridge.py`: the subject is the artifact a user actually
gets from `view.export.html(...)`, with the same template and the same embedded
runtime. The host pages it is dropped into are written by the suite, because
each one *is* the scenario.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from molsysviewer.demo import demo


def main() -> None:
    view = demo["dialanine"]
    view.widget.send = lambda *_args, **_kwargs: None  # type: ignore[method-assign]

    output_dir = Path(tempfile.mkdtemp(prefix="molsysviewer-colour-"))
    output = output_dir / "view.html"
    view.export.html(str(output), skip_digestion=True)

    print(json.dumps({"directory": str(output_dir), "page": output.name}))


if __name__ == "__main__":
    main()
