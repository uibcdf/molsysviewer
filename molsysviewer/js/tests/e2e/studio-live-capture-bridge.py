"""One real Studio authority, with its connector loop alive between requests."""

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import molsysviewer as msv
from molsysviewer import FigureSpec


def inspect_artifact(view, event):
    if event.get("studio_inspect"):
        return {"authority_state": view.export_state()}
    if "studio_artifact" not in event:
        return False
    path = Path(event["studio_artifact"])
    if event.get("file_kind") == "session":
        with zipfile.ZipFile(path) as archive:
            return {
                "saved_state": json.loads(archive.read("state.json")),
                "session_manifest": json.loads(archive.read("manifest.json")),
                "session_members": archive.namelist(),
            }
    return {"saved_state": json.loads(path.read_text())}


def main():
    source = msv.demo["pentalanine"]
    try:
        view = msv.new_view(source.molsys, structure_indices=[0, 8, 3], controls_mode="compact")
    finally:
        source.close()
    view.whole.set_representation("ball-and-stick")
    view.set_figure_spec(FigureSpec(scale=1.5, background="white"))
    view.annotations.add("Saved live canvas", position="[1, 2, 3] nm", tag="live-note")
    view.interactions.hbonds.get_buch_hbonds(name="live-review", structure_indices="all", distance_threshold="0.4 nm")
    view.interactions.add("live-review", tag="live-hbonds")
    module_path = Path(__file__).with_name("canvas-popup-bridge.py")
    spec = importlib.util.spec_from_file_location("studio_canvas_fixture", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.serve(view, inspect_artifact, async_processing=True)


if __name__ == "__main__":
    main()
