"""Produce a real exported page for the framing E2E to open.

Not a fixture built in TypeScript: the point of this suite is the artifact a
user actually gets from `view.export.html(...)`, so it has to come out of the
Python exporter, with the same template, the same embedded runtime and the same
absence of a kernel behind it.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import molsysmt as msm

from molsysviewer.demo import demo


def main() -> None:
    view = demo["dialanine"]
    view.widget.send = lambda *_args, **_kwargs: None  # type: ignore[method-assign]

    output_dir = Path(tempfile.mkdtemp(prefix="molsysviewer-framing-"))
    output = output_dir / "view.html"
    view.export.html(str(output), skip_digestion=True)

    print(json.dumps({
        "page": str(output),
        "n_atoms": int(msm.get(view.molsys, n_atoms=True)),
    }))


if __name__ == "__main__":
    main()
