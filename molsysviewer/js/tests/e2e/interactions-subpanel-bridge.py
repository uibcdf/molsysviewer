"""Fresh scientific fixtures with persistent JSON-lines transport.

Imports stay warm; each request owns a fresh view. Fixture files survive until
worker shutdown, allowing later scenarios to import earlier fixture files.
"""

import contextlib
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from runpy import run_path

ROOT = Path(__file__).resolve().parents[4]
if os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") == "1":
    run_path(str(ROOT / "devtools/_fixture_namespace.py"))["expose_fixture_namespace"](ROOT)
else:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))


def replay(events, family, fixture_root):
    """Replay one independent scenario against a fresh real viewer."""
    import molsysmt as msm
    from molsysviewer.interactions import _to_plain

    from test_interactions_scene import view as scene_fixture

    fixture_file = None
    if family == "pentalanine_scope":
        import molsysviewer as msv

        demo = msv.demo["pentalanine"]
        try:
            view = msv.new_view(demo.molsys, structure_indices=[0, 8, 3])
        finally:
            demo.close()
    elif family:
        from devtools.interaction_family_fixtures import make_family_view

        view = make_family_view(family).view
    else:
        view = scene_fixture.__wrapped__()
    try:
        if not family:
            view.interactions.add("contacts", tag="hb")
            view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="hb")
            view.measurements.add_distance(selection_a=[0], selection_b=[1], tag="hb")
            fixture_dir = Path(tempfile.mkdtemp(prefix="scenario-", dir=fixture_root))
            fixture_file = fixture_dir / "contacts.h5msm"
            msm.h5msm.write_layers(
                str(fixture_file), interactions={"contacts": view.interactions.get_analysis("contacts")}
            )
        view._ready = True
        sent = []
        view.widget.send = sent.append
        initial = view._build_embedded_runtime_snapshot()
        batches = []
        for event in events:
            view._handle_frontend_event(event)
            batches.append(list(sent))
            sent.clear()
        return _to_plain(
            {
                "initial_messages": initial,
                "message_batches": batches,
                "series": view.interactions._static_messages(),
                "summary": view.interactions._summary_message(),
                "inspection": view.interactions.inspect("hb") if view.interactions.contains("hb") else None,
                "fixture_file": str(fixture_file) if fixture_file is not None else None,
                "state": view.export_state(),
                "calculation_scopes": {
                    item["name"]: view.interactions.get_analysis(item["name"]).evaluation_scope
                    for item in view.interactions.analyses()
                }
                if family == "pentalanine_scope"
                else {},
            }
        )
    finally:
        view.close()


def main():
    if "--serve" not in sys.argv:
        # Preserve the one-shot interface, including its externally reusable file.
        fixture_root = tempfile.mkdtemp(prefix="msv-interactions-e2e-")
        raw = sys.stdin.read().strip()
        with contextlib.redirect_stdout(sys.stderr):
            result = replay(json.loads(raw) if raw else [], sys.argv[1] if len(sys.argv) > 1 else None, fixture_root)
        print(json.dumps(result, allow_nan=False))
        return
    with tempfile.TemporaryDirectory(prefix="msv-interactions-e2e-") as fixture_root:
        for line in sys.stdin:
            request_id = None
            try:
                request = json.loads(line)
                request_id = request["id"]
                with contextlib.redirect_stdout(sys.stderr):
                    result = replay(request.get("events", []), request.get("family"), fixture_root)
                response = {"id": request_id, "result": result}
            except Exception:
                response = {"id": request_id, "error": traceback.format_exc()}
            print(json.dumps(response, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
