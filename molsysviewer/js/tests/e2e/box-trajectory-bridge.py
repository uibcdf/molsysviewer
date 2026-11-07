"""Real pentalanine exports with independent row-vector cell controls."""

import json
import sys
from pathlib import Path

import molsysmt as msm
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import molsysviewer as msv


def main():
    cells = np.array(
        [
            [[3, 0, 0], [0, 4, 0], [0, 0, 5]],
            [[0, 4, 0], [-5, 0, 0], [0, 0, 6]],
            [[4, 1, 0], [1, 5, 0], [1, 1, 6]],
        ],
        dtype=float,
    )
    with msv.demo["pentalanine"] as source:
        with source.extract(structure_indices=[0, 8, 3]) as view:
            msm.set(view.molsys, box=msv.pyunitwizard.quantity(cells, "nm"))
            view.apply_system_edit(view.molsys)
            view.show_box(color="red", width="0.125 nm", alpha=0.7)
            if sys.argv[1] == "--serve":

                def action(owner, event):
                    command = event.get("box_fixture")
                    if command is None:
                        return False
                    if command == "show":
                        owner.show_box(color="red", width="0.125 nm", alpha=0.7, structure_indices=event["index"])
                    elif command == "style":
                        owner.show_box(color="blue", width="0.08 nm", alpha=0.4, structure_indices=0)
                    elif command == "hide":
                        owner.hide_box()
                    elif command == "frame":
                        owner.player.go_to_structure(event["index"])
                    elif command == "replace":
                        owner.set_box(msv.pyunitwizard.quantity(cells * 2, "nm"))
                    elif command == "clear":
                        owner.clear_decorations(shapes=True)
                    else:
                        raise ValueError(f"Unknown box command: {command}")
                    return {"box_state": owner.export_state().get("box_display")}

                # Reuse the persistent widget authority; only notebook comms
                # are transported by the browser fixture.
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "canvas_popup_bridge", Path(__file__).with_name("canvas-popup-bridge.py")
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.serve(view, action)
                return
            directory = Path(sys.argv[1])
            view.export.html(directory / "box.html")
            (directory / "fixture.json").write_text(
                json.dumps(
                    {
                        "page": str(directory / "box.html"),
                        "boxes_angstrom": (cells * 10).tolist(),
                    }
                )
            )


if __name__ == "__main__":
    main()
