from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from molsysviewer import MolSysView, systems


def load_message(source: Path) -> dict:
    view = MolSysView()
    try:
        view.load(
            source,
            structure_indices=[0],
            mode="replace",
            skip_digestion=True,
        )
        return next(
            message
            for message in reversed(view._message_history)  # noqa: SLF001
            if message.get("op") == "load_molsys_payload"
        )
    finally:
        view.close()


def main() -> None:
    print(
        json.dumps(
            {
                "first": load_message(systems.dialanine.path),
                "second": load_message(systems.pentalanine.path),
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
