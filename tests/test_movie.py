"""Unit tests for MovieManager (Phase 1 — Python data model).

These tests exercise the timeline construction, serialization, and
convenience builders without requiring a live viewer or JS runtime.
"""
from __future__ import annotations

import json
import math
import pytest

from molsysviewer.viewer.movie import MovieManager, _MOLSYSMOVIE_VERSION


# ── DummyView ──────────────────────────────────────────────────────────────────

class DummyCamera:
    def __init__(self, snapshot=None):
        self._snapshot = snapshot or {
            "position": [10.0, 0.0, 0.0],
            "target":   [0.0,  0.0, 0.0],
            "up":       [0.0,  1.0, 0.0],
        }

    def get_snapshot(self, *, skip_digestion=False, **_kwargs):
        return self._snapshot


class DummyPlayer:
    def __init__(self, n_structures=10):
        self.n_structures = n_structures


class DummyView:
    def __init__(self, n_structures=10, camera_snapshot=None):
        self.camera = DummyCamera(camera_snapshot)
        self.player = DummyPlayer(n_structures)
        self.sent_messages: list[dict] = []
        self._movie_export_frames: list | None = None
        self._movie_export_done: bool = False

    def _send(self, msg: dict) -> None:
        self.sent_messages.append(msg)

    def _send_runtime_only(self, msg: dict) -> None:
        self.sent_messages.append(msg)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_movie(n_structures=10, camera_snapshot=None):
    view = DummyView(n_structures=n_structures, camera_snapshot=camera_snapshot)
    return MovieManager(view)


SNAP_A = {"position": [10.0, 0.0, 0.0], "target": [0.0, 0.0, 0.0], "up": [0.0, 1.0, 0.0]}
SNAP_B = {"position": [0.0, 10.0, 0.0], "target": [0.0, 0.0, 0.0], "up": [0.0, 0.0, 1.0]}


# ── add_keyframe ───────────────────────────────────────────────────────────────

def test_add_keyframe_basic():
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A)
    m.add_keyframe(3000.0, camera=SNAP_B)

    assert len(m.keyframes) == 2
    assert m.keyframes[0]["time_ms"] == 0.0
    assert m.keyframes[1]["time_ms"] == 3000.0
    assert m.keyframes[0]["camera"]["position"] == [10.0, 0.0, 0.0]


def test_add_keyframe_structure_index():
    m = make_movie()
    m.add_keyframe(0.0, structure_index=0)
    m.add_keyframe(5000.0, structure_index=9)

    assert m.keyframes[0]["structure_index"] == 0
    assert m.keyframes[1]["structure_index"] == 9


def test_add_keyframe_layer_visibility():
    m = make_movie()
    m.add_keyframe(0.0, layer_visibility={"pocket": True, "solvent": False})

    lv = m.keyframes[0]["layer_visibility"]
    assert lv["pocket"] is True
    assert lv["solvent"] is False


def test_add_keyframe_easing_stored():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(1000.0, easing="ease-in-out")

    assert m.keyframes[1]["easing"] == "ease-in-out"


def test_add_keyframe_invalid_easing():
    m = make_movie()
    with pytest.raises(ValueError, match="easing"):
        m.add_keyframe(0.0, easing="bounce")


def test_add_keyframe_non_increasing_time():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(1000.0)
    with pytest.raises(ValueError, match="strictly greater"):
        m.add_keyframe(500.0)


def test_add_keyframe_equal_time_rejected():
    m = make_movie()
    m.add_keyframe(0.0)
    with pytest.raises(ValueError, match="strictly greater"):
        m.add_keyframe(0.0)


def test_add_keyframe_invalid_camera_missing_key():
    m = make_movie()
    with pytest.raises(ValueError, match="missing required key"):
        m.add_keyframe(0.0, camera={"position": [0, 0, 0], "target": [1, 0, 0]})


def test_add_keyframe_no_fields_is_valid():
    m = make_movie()
    m.add_keyframe(0.0)
    assert m.keyframes[0] == {"time_ms": 0.0, "easing": "linear"}


# ── add_visibility_transition ──────────────────────────────────────────────────

def test_visibility_transition_inserts_new_keyframe():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(5000.0)
    m.add_visibility_transition("pocket", True, at_time_ms=2500.0)

    times = [kf["time_ms"] for kf in m.keyframes]
    assert 2500.0 in times
    middle = next(kf for kf in m.keyframes if kf["time_ms"] == 2500.0)
    assert middle["layer_visibility"]["pocket"] is True


def test_visibility_transition_merges_into_existing_keyframe():
    m = make_movie()
    m.add_keyframe(0.0, layer_visibility={"A": True})
    m.add_visibility_transition("B", False, at_time_ms=0.0)

    lv = m.keyframes[0]["layer_visibility"]
    assert lv["A"] is True
    assert lv["B"] is False
    assert len(m.keyframes) == 1  # no new keyframe added


def test_visibility_transition_sorted_insertion():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(4000.0)
    m.add_visibility_transition("X", True, at_time_ms=1000.0)
    m.add_visibility_transition("Y", True, at_time_ms=3000.0)

    times = [kf["time_ms"] for kf in m.keyframes]
    assert times == sorted(times)


# ── clear / duration_ms ────────────────────────────────────────────────────────

def test_clear_resets_timeline():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(3000.0)
    m.clear()

    assert m.keyframes == []
    assert m.duration_ms == 0.0


def test_duration_ms_empty():
    m = make_movie()
    assert m.duration_ms == 0.0


def test_duration_ms_reflects_last_keyframe():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(7500.0)
    assert m.duration_ms == 7500.0


# ── info ───────────────────────────────────────────────────────────────────────

def test_info_empty():
    m = make_movie()
    i = m.info()
    assert i["n_keyframes"] == 0
    assert i["duration_ms"] == 0.0
    assert i["has_camera"] is False
    assert i["has_structure_sweep"] is False
    assert i["has_visibility_transitions"] is False


def test_info_populated():
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A, structure_index=0)
    m.add_keyframe(5000.0, camera=SNAP_B, structure_index=9,
                   layer_visibility={"pocket": True})
    i = m.info()
    assert i["n_keyframes"] == 2
    assert i["duration_ms"] == 5000.0
    assert i["has_camera"] is True
    assert i["has_structure_sweep"] is True
    assert i["has_visibility_transitions"] is True


# ── serialization ──────────────────────────────────────────────────────────────

def test_to_dict_round_trip():
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A, structure_index=0)
    m.add_keyframe(5000.0, camera=SNAP_B, layer_visibility={"X": False})
    data = m.to_dict()

    assert data["molsysmovie_version"] == _MOLSYSMOVIE_VERSION
    assert len(data["keyframes"]) == 2

    m2 = make_movie()
    m2.from_dict(data)
    assert m2.keyframes == m.keyframes


def test_from_dict_wrong_version():
    m = make_movie()
    with pytest.raises(ValueError, match="molsysmovie_version"):
        m.from_dict({"molsysmovie_version": 99, "keyframes": []})


def test_from_dict_missing_time_ms():
    m = make_movie()
    with pytest.raises(ValueError, match="missing 'time_ms'"):
        m.from_dict({
            "molsysmovie_version": _MOLSYSMOVIE_VERSION,
            "keyframes": [{"easing": "linear"}],
        })


def test_from_dict_non_increasing_times():
    m = make_movie()
    with pytest.raises(ValueError, match="strictly greater"):
        m.from_dict({
            "molsysmovie_version": _MOLSYSMOVIE_VERSION,
            "keyframes": [
                {"time_ms": 0.0, "easing": "linear"},
                {"time_ms": 0.0, "easing": "linear"},
            ],
        })


def test_save_and_load(tmp_path):
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A)
    m.add_keyframe(3000.0, camera=SNAP_B, structure_index=5)
    path = tmp_path / "timeline.json"
    m.save(path)

    assert path.exists()
    raw = json.loads(path.read_text())
    assert raw["molsysmovie_version"] == _MOLSYSMOVIE_VERSION

    m2 = make_movie()
    m2.load(path)
    assert m2.keyframes == m.keyframes


def test_to_dict_is_json_serializable():
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A, structure_index=0,
                   layer_visibility={"r": True})
    m.add_keyframe(2000.0, camera=SNAP_B)
    # Should not raise
    json.dumps(m.to_dict())


# ── add_camera_orbit ───────────────────────────────────────────────────────────

def test_add_camera_orbit_produces_keyframes():
    m = make_movie()
    m.add_camera_orbit(duration_ms=5000.0, n_turns=1, n_keyframes=36)

    # total_kf = 36 * 1 + 1 = 37
    assert len(m.keyframes) == 37
    assert m.duration_ms == 5000.0


def test_add_camera_orbit_first_last_positions_close():
    """A full orbit should return to (approximately) the starting position."""
    snap = {
        "position": [10.0, 0.0, 0.0],
        "target":   [0.0,  0.0, 0.0],
        "up":       [0.0,  1.0, 0.0],
    }
    m = make_movie(camera_snapshot=snap)
    m.add_camera_orbit(duration_ms=5000.0, n_turns=1, n_keyframes=36)

    first_pos = m.keyframes[0]["camera"]["position"]
    last_pos  = m.keyframes[-1]["camera"]["position"]
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(first_pos, last_pos)))
    assert dist < 1e-6


def test_add_camera_orbit_constant_radius():
    snap = {
        "position": [10.0, 0.0, 0.0],
        "target":   [0.0,  0.0, 0.0],
        "up":       [0.0,  1.0, 0.0],
    }
    m = make_movie(camera_snapshot=snap)
    m.add_camera_orbit(duration_ms=5000.0, n_turns=1, n_keyframes=12)

    radii = [
        math.sqrt(sum((p - t) ** 2 for p, t in zip(
            kf["camera"]["position"], kf["camera"]["target"]
        )))
        for kf in m.keyframes
    ]
    assert all(abs(r - radii[0]) < 1e-9 for r in radii)


def test_add_camera_orbit_appends_after_existing():
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A)
    m.add_camera_orbit(duration_ms=3000.0, n_turns=1, n_keyframes=6)

    # First orbit keyframe merges camera into the existing t=0 keyframe
    assert m.keyframes[0]["time_ms"] == 0.0
    # Last keyframe at t=3000
    assert m.keyframes[-1]["time_ms"] == pytest.approx(3000.0)


def test_add_camera_orbit_invalid_easing():
    m = make_movie()
    with pytest.raises(ValueError, match="easing"):
        m.add_camera_orbit(easing="wobble")


# ── add_structure_sweep ────────────────────────────────────────────────────────

def test_add_structure_sweep_basic():
    m = make_movie(n_structures=10)
    m.add_structure_sweep(from_index=0, to_index=9, duration_ms=5000.0)

    assert len(m.keyframes) == 10
    assert m.keyframes[0]["structure_index"] == 0
    assert m.keyframes[-1]["structure_index"] == 9
    assert m.duration_ms == pytest.approx(5000.0)


def test_add_structure_sweep_uses_player_n_structures():
    m = make_movie(n_structures=5)
    m.add_structure_sweep(duration_ms=2000.0)

    indices = [kf["structure_index"] for kf in m.keyframes]
    assert indices == [0, 1, 2, 3, 4]


def test_add_structure_sweep_end_time_ms():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_structure_sweep(
        from_index=0, to_index=4,
        start_time_ms=1000.0, end_time_ms=6000.0,
    )
    last = m.keyframes[-1]
    assert last["time_ms"] == pytest.approx(6000.0)
    assert last["structure_index"] == 4


def test_add_structure_sweep_from_gt_to_raises():
    m = make_movie()
    with pytest.raises(ValueError, match="from_index"):
        m.add_structure_sweep(from_index=5, to_index=2, duration_ms=1000.0)


def test_add_structure_sweep_negative_duration_raises():
    m = make_movie()
    with pytest.raises(ValueError, match="positive"):
        m.add_structure_sweep(from_index=0, to_index=4, duration_ms=-100.0)


def test_add_structure_sweep_both_duration_and_end_raises():
    m = make_movie()
    with pytest.raises(ValueError, match="not both"):
        m.add_structure_sweep(
            from_index=0, to_index=4,
            duration_ms=1000.0, end_time_ms=2000.0,
        )


def test_add_structure_sweep_neither_duration_nor_end_raises():
    m = make_movie()
    with pytest.raises(ValueError, match="duration_ms or end_time_ms"):
        m.add_structure_sweep(from_index=0, to_index=4)


# ── play / stop ────────────────────────────────────────────────────────────────

def test_play_sends_message():
    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A)
    m.add_keyframe(3000.0, camera=SNAP_B)
    m.play()
    msgs = m._view.sent_messages
    assert len(msgs) == 1
    assert msgs[0]["op"] == "play_movie"
    assert len(msgs[0]["keyframes"]) == 2
    assert msgs[0]["loop"] is False


def test_play_loop_flag():
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(1000.0)
    m.play(loop=True)
    assert m._view.sent_messages[-1]["loop"] is True


def test_play_requires_two_keyframes():
    m = make_movie()
    with pytest.raises(ValueError):
        m.play()
    m.add_keyframe(0.0)
    with pytest.raises(ValueError):
        m.play()


def test_stop_sends_message():
    m = make_movie()
    m.stop()
    msgs = m._view.sent_messages
    assert len(msgs) == 1
    assert msgs[0]["op"] == "stop_movie"


# ── export ────────────────────────────────────────────────────────────────────

def test_export_requires_imageio():
    """export() raises ImportError if imageio is absent (hard to mock; skip if present)."""
    import importlib
    if importlib.util.find_spec("imageio"):
        pytest.skip("imageio is installed; cannot test ImportError path")
    m = make_movie()
    m.add_keyframe(0.0)
    m.add_keyframe(1000.0)
    with pytest.raises(ImportError, match="imageio"):
        m.export("out.mp4")


def test_export_requires_two_keyframes():
    imageio = pytest.importorskip("imageio")
    m = make_movie()
    with pytest.raises(ValueError):
        m.export("out.mp4")
    m.add_keyframe(0.0)
    with pytest.raises(ValueError):
        m.export("out.mp4")


def test_export_sends_correct_message(tmp_path):
    """export() sends play_movie with mode=export and correct total_frames."""
    import threading, base64
    imageio = pytest.importorskip("imageio")
    import numpy as np

    m = make_movie()
    m.add_keyframe(0.0, camera=SNAP_A)
    m.add_keyframe(1000.0, camera=SNAP_B)

    # 1 000 ms at 4 fps → floor(1000/1000*4)+1 = 5 frames
    fps = 4
    total_frames = 5

    # Build a tiny 1×1 PNG encoded as a data URI
    fake_png = imageio.imwrite("<bytes>", np.zeros((1, 1, 3), dtype="uint8"), format="png")
    data_uri = "data:image/png;base64," + base64.b64encode(fake_png).decode()

    result = {}

    def simulate_js():
        """Wait until the play_movie message is sent, then feed frames."""
        import time
        deadline = time.monotonic() + 5.0
        while not m._view.sent_messages:
            if time.monotonic() > deadline:
                return
            time.sleep(0.01)
        m._view._movie_export_frames = [
            {"data_uri": data_uri, "frame_index": i, "total_frames": total_frames}
            for i in range(total_frames)
        ]
        m._view._movie_export_done = True

    t = threading.Thread(target=simulate_js, daemon=True)
    t.start()
    out = m.export(tmp_path / "out.gif", fps=fps)
    t.join(timeout=5)

    # Verify the message
    msg = m._view.sent_messages[0]
    assert msg["op"] == "play_movie"
    assert msg["mode"] == "export"
    assert msg["fps"] == fps
    assert msg["total_frames"] == total_frames

    # Verify the output file was written
    assert out.exists()


def test_export_decode_frame_helper():
    """_decode_frame round-trips a tiny PNG correctly."""
    import base64
    imageio = pytest.importorskip("imageio")
    import numpy as np
    from molsysviewer.viewer.movie import _decode_frame

    arr = np.zeros((2, 2, 3), dtype="uint8")
    arr[0, 0] = [255, 0, 0]
    png_bytes = imageio.imwrite("<bytes>", arr, format="png")
    uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    result = _decode_frame(uri)
    assert result.shape[:2] == (2, 2)
    assert result[0, 0, 0] == 255
