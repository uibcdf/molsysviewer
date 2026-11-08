"""Real trajectory/camera capture pilot; production negotiation remains v1."""

import asyncio
import importlib.util
import json
import sys
import time
import traceback
import zipfile
from collections import deque
from pathlib import Path

import molsysmt as msm
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import molsysviewer as msv


def main():
    with msv.demo["pentalanine"] as source:
        view = source.extract(structure_indices=[0, 8, 3])
    coordinates = msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="nm").copy()
    coordinates[1, 1] += [100, 100, 100]
    cells = np.array(
        [[[3, 0, 0], [0, 4, 0], [0, 0, 5]], [[0, 4, 0], [-5, 0, 0], [0, 0, 6]], [[4, 1, 0], [1, 5, 0], [1, 1, 6]]],
        dtype=float,
    )
    msm.set(view.molsys, coordinates=msv.pyunitwizard.quantity(coordinates, "nm"))
    msm.set(view.molsys, box=msv.pyunitwizard.quantity(cells, "nm"))
    view.apply_system_edit(view.molsys)
    view.show_box(color="red", width="0.125 nm", alpha=0.7)
    view.whole.set_representation("ball-and-stick")
    view.measurements.add_distance([0], [1], tag="moving-distance")
    view.annotations.add(
        "Moving anchor",
        atom_indices=[0],
        offset_mode="camera",
        offset=(6.0, 8.0, 5.0),
        leader_line=True,
        leader_line_style="solid",
        label_style={"size_em": 1.0, "background": True, "background_opacity": 0.8},
        tag="moving-note",
    )
    view.annotations.add("World anchor", atom_indices=[0], offset_mode="world", offset="[1, 0, 0] nm", tag="world-note")
    view.annotations.add("Absolute anchor", position="[-1, -1, 0] nm", offset_mode="world", tag="absolute-note")
    view.shapes.add_sphere(
        structure_centers="[[0, 0, 0], [1, 0, 0], [2, 0, 0]] nm", radius="0.1 nm", tag="moving-marker"
    )
    view.interactions.hbonds.get_buch_hbonds(
        name="moving-analysis", structure_indices="all", distance_threshold="0.4 nm"
    )
    view.interactions.add("moving-analysis", tag="moving-hbonds")
    # This fixture receives semantics, not the separate 25-ms performance budget.
    view._dynamic_region_evaluation_budget_ms = float("inf")
    near = view.regions.add(selection="atom_index==1 within 1 nm without pbc of atom_index==0", tag="moving-near")
    near.mode = "dynamic"
    near.set_representation("ball-and-stick")
    original = view.molsys
    jobs = {}
    held = []
    holding = False
    started = time.monotonic()
    timeline = deque(maxlen=128)

    def observe(name, **details):
        timeline.append({"ms": round((time.monotonic() - started) * 1000, 3), "name": name, **details})

    async def save(path, kind):
        observe("save_started", kind=kind)
        try:
            method = view.save_session_async if kind == "session" else view.save_state_async
            await method(path, timeout=12)
            jobs[path] = {"done": True, "ok": True}
            observe("save_complete", kind=kind)
        except Exception as error:
            observe("save_failed", kind=kind, error_type=type(error).__name__)
            jobs[path] = {
                "done": True,
                "ok": False,
                "error_type": type(error).__name__,
                "reason": getattr(error, "reason", None),
                "message": str(error),
                "traceback": traceback.format_exc(),
            }

    def action(owner, event):
        nonlocal holding
        payload = event.get("payload", event)
        if payload.get("event") in {
            "request_dynamic_region_evaluation",
            "request_interaction_frame",
            "trajectory_frame_changed",
            "visual_state_snapshot",
        }:
            observe(payload["event"], frame=payload.get("frame"), holding=holding)
        if payload.get("event") == "request_dynamic_region_evaluation" and holding:
            held.append(event)
            return {"moving_fixture_held": {"frame": payload.get("frame"), "count": len(held)}}
        command = event.get("moving_fixture")
        if command is None:
            return False
        if command != "inspect":
            observe(command, held=len(held), pending_saves=sum(not job["done"] for job in jobs.values()))
        if command == "enable":
            # Exercise the new receiver without advertising a shipped capability.
            owner._frontend_capabilities["visual_state_capture"] = [1, 2]
        elif command == "play":
            owner.player.play(fps=2, mode="ping-pong")
            owner.scene.spin(True, speed=0.05)
        elif command == "empty_frame":
            # An explicit stopped-trajectory control receives a genuinely empty
            # dynamic selection; it is separate from uninterrupted capture.
            owner.player.pause()
            owner.player.go_to_structure(1)
        elif command == "presentation":
            owner.player.pause()
            owner.scene.spin(False)
            owner.player.go_to_structure(0)
            owner.hide_box()
            owner.whole.hide()
            near.hide()
            owner.shapes.hide("moving-marker")
            owner.measurements.hide("moving-distance")
            owner.interactions.hide("moving-hbonds")
            owner.camera.set_snapshot(
                {"position": [0, 0, 100], "target": [0, 0, 0], "up": [0, 1, 0], "radius": 30, "radiusMax": 100}
            )
        elif command == "camera":
            owner.camera.set_snapshot(event["snapshot"])
        elif command == "projection":
            owner.scene.set_projection(event["mode"])
        elif command == "hold":
            holding = True
        elif command == "release":
            holding = False
            for message in held[:]:
                observe("held_delivery_start", frame=message.get("payload", message).get("frame"))
                owner._handle_inbound_message(message)
                observe("held_delivery_complete")
            held.clear()
        elif command == "save":
            path = event["path"]
            jobs[path] = {"done": False}
            asyncio.create_task(save(path, event["kind"]))
        elif command == "inspect":
            return {
                "jobs": dict(jobs),
                "held": len(held),
                "same_molsys": owner.molsys is original,
                "coordinates_unchanged": bool(
                    np.array_equal(msv.pyunitwizard.get_value(owner.get_coordinates(), to_unit="nm"), coordinates)
                ),
                "authority_state": owner.export_state(),
                "coordinates_angstrom": (coordinates * 10).tolist(),
                "cells_angstrom": (cells * 10).tolist(),
                "camera_offset": [6.0, 8.0, 5.0],
                "timeline": list(timeline),
            }
        elif command == "artifact":
            path = event["path"]
            if event["kind"] == "session":
                with zipfile.ZipFile(path) as archive:
                    saved = json.loads(archive.read("state.json"))
                restored = msv.load_session(path)
            else:
                saved = json.loads(Path(path).read_text())
                restored = msv.new_view(owner.molsys)
                restored.load_state(path)
            with restored:
                return {
                    "saved_state": saved,
                    "restored_state": restored.export_state(),
                    "restored_region_atoms": restored.regions["moving-near"].atom_indices,
                }
        else:
            raise ValueError(f"Unknown moving-capture command: {command}")
        return True

    spec = importlib.util.spec_from_file_location(
        "moving_canvas_fixture", Path(__file__).with_name("canvas-popup-bridge.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.serve(view, action, async_processing=True)


if __name__ == "__main__":
    main()
