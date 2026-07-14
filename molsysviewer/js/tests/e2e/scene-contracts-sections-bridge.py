from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from molsysviewer.demo import demo


def main() -> None:
    source = demo["dialanine"]
    source.scene.add_section(
        point=[0.1, 0.2, 0.3],
        normal=[2.0, 0.0, 0.0],
        invert=True,
        tag="cut",
    )
    document = source.export_state()

    restored = demo["dialanine"]
    sent: list[dict] = []
    restored.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    restored._ready = True  # noqa: SLF001
    restored.import_state(document)

    section = restored.scene.sections()[0]
    section.set_point([0.4, 0.2, 0.3])
    set_sections = [message for message in sent if message.get("op") == "set_sections"]
    print(json.dumps({
        "document": document,
        "restored": restored.export_state()["sections"],
        "message": set_sections[-1],
    }))


if __name__ == "__main__":
    main()
