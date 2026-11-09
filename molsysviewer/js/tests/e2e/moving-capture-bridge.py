"""Real trajectory/camera capture pilot; production negotiation remains v1."""

import asyncio
import importlib.util
import json
import sys
import time
import traceback
import zipfile
from collections import deque
from copy import deepcopy
from pathlib import Path

import molsysmt as msm
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import molsysviewer as msv


def configure_moving_scene(view):
    """Use the same real science and sparse scene in browser/native host guards."""
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
    return coordinates, cells, near


def main():
    with msv.demo["pentalanine"] as source:
        view = source.extract(structure_indices=[0, 8, 3])
    coordinates, cells, near = configure_moving_scene(view)
    original = view.molsys
    jobs = {}
    held = []
    holding = False
    holding_bootstrap = False
    held_bootstraps = []
    original_send = None
    started = time.monotonic()
    timeline = deque(maxlen=128)

    def observe(name, **details):
        timeline.append({"ms": round((time.monotonic() - started) * 1000, 3), "name": name, **details})

    async def save(path, kind, timeout=12):
        observe("save_started", kind=kind)
        try:
            method = view.save_session_async if kind == "session" else view.save_state_async
            await method(path, timeout=timeout)
            jobs[path] = {"done": True, "ok": True}
            observe("save_complete", kind=kind)
        except Exception as error:
            observe("save_failed", kind=kind, error_type=type(error).__name__)
            facts = getattr(error, "extra", None)
            jobs[path] = {
                "done": True,
                "ok": False,
                "error_type": type(error).__name__,
                "reason": facts.get("reason") if isinstance(facts, dict) else None,
                "diagnostic_code": getattr(error, "code", None),
                "message": str(error),
                "traceback": traceback.format_exc(),
            }

    def action(owner, event):
        nonlocal holding, holding_bootstrap, original_send
        payload = event.get("payload", event)
        if payload.get("event") in {
            "request_dynamic_region_evaluation",
            "request_interaction_frame",
            "trajectory_frame_changed",
            "visual_state_snapshot",
        }:
            pending = owner._frontend_requests._pending.get(payload.get("request_id"))
            observe(
                payload["event"],
                frame=payload.get("frame"),
                holding=holding,
                request_id=payload.get("request_id"),
                query_endpoint_id=payload.get("_query_endpoint_id"),
                error_type=payload.get("error_type"),
                ok=payload.get("ok"),
                ticket_remaining_ms=(pending.deadline - time.monotonic()) * 1000 if pending is not None else None,
                ticket_pending=pending is not None,
            )
        if payload.get("action") == "save_work_file":
            observe("save_work_file", request_id=payload.get("request_id"), holding=holding)
        if payload.get("event") == "request_dynamic_region_evaluation" and holding:
            held.append(event)
            return {"moving_fixture_held": {"frame": payload.get("frame"), "count": len(held)}}
        command = event.get("moving_fixture")
        if command is None:
            return False
        if command != "inspect":
            observe(
                command,
                held=len(held),
                pending_saves=sum(not job["done"] for job in jobs.values()) + len(owner._work_file_saves._pending),
            )
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
        elif command == "hold_bootstrap":
            holding_bootstrap = True
            if original_send is None:
                original_send = owner.widget.send

                def filter_bootstrap(content, buffers=None):
                    payload = content.get("payload", content)
                    if holding_bootstrap and payload.get("event") == "popup_scene_snapshot":
                        held_bootstraps.append((deepcopy(content), buffers))
                    else:
                        original_send(content, buffers=buffers)

                owner.widget.send = filter_bootstrap
        elif command == "release_bootstrap":
            holding_bootstrap = False
            for content, buffers in held_bootstraps:
                original_send(content, buffers=buffers)
            held_bootstraps.clear()
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
            asyncio.create_task(save(path, event["kind"], event.get("timeout", 12)))
        elif command == "freeze_dynamic":
            owner._clear_dynamic_region_cache(near.uid)
            owner._dynamic_region_evaluation_budget_ms = -1
            owner._handle_dynamic_region_evaluation_request({"frame": 0})
        elif command == "close_view":
            owner.close()
        elif command == "inspect":
            if owner.closed:
                return {
                    "jobs": dict(jobs),
                    "closed": True,
                    "pending_studio_saves": len(owner._work_file_saves._pending),
                    "pending_captures": len(owner._frontend_requests._pending),
                }
            return {
                "jobs": dict(jobs),
                "held": len(held),
                "held_bootstraps": len(held_bootstraps),
                "pending_studio_saves": len(owner._work_file_saves._pending),
                "pending_captures": len(owner._frontend_requests._pending),
                "endpoint_modes": dict(owner._endpoint_transfers.modes),
                "region_mode": near.mode,
                "region_atoms": near.atom_indices,
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
