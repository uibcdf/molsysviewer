"""Where the user was looking, and what they were looking at.

Slice 2 of issue #38. Everything else in a state document describes objects the user
built; this describes the vantage point. A scene restored onto the right atoms but with a
different camera and a different frame is not the scene that was saved -- and for a
trajectory the frame is a scientific claim, not a preference.

The camera lives in the browser. Python knows it because the frontend debounces camera
changes back every 300 ms, which is why `export_state` can read it for free and must
never ask for it: it runs on every undoable operation. `save_state` does ask, because a
save is a deliberate act and can afford one round trip.
"""

from __future__ import annotations

import json
import warnings

import molsysmt as msm
import pytest
from molsysviewer._private.smonitor.warnings import StateStructureIndexOutOfRangeWarning
from molsysviewer.demo import demo

import molsysviewer as msv


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def _with_camera(view, camera=None):
    view._ready = True  # noqa: SLF001
    view._last_camera_snapshot = camera or {  # noqa: SLF001
        "position": [1.0, 2.0, 3.0],
        "target": [0.0, 0.0, 0.0],
    }
    return view


def test_the_camera_and_the_frame_survive_a_round_trip():
    view = _with_camera(_mute(demo["pentalanine"]))
    view.player.go_to_structure(500)
    view.player.set_fps(12)
    document = view.export_state()

    view.player.go_to_structure(0)
    view.player.set_fps(30)
    view._last_camera_snapshot = None  # noqa: SLF001
    view.import_state(document)

    assert view.camera.get_snapshot() == {"position": [1.0, 2.0, 3.0], "target": [0.0, 0.0, 0.0]}
    assert view.player.index == 500
    assert view.player.fps == 12


def test_a_viewer_that_was_never_displayed_writes_no_camera_and_imports_cleanly():
    """Contract S5's additive-key rule again: the key is absent, not null.

    This is the case that was worth asking about -- there really is a viewer with no
    camera, and it is the ordinary one in a headless run or before the frontend is ready.
    """
    view = _mute(demo["dialanine"])
    view._last_camera_snapshot = None  # noqa: SLF001

    document = view.export_state()

    assert "camera" not in document.get("view", {})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        view.import_state(document)


def test_a_frame_the_loaded_trajectory_does_not_have_is_reported_not_approximated():
    """The fingerprint is topological, so the same system with fewer frames matches it.

    Moving to the nearest available frame would answer a question the document did not
    ask, and the viewer would show a structure nobody chose.
    """
    source = _mute(demo["pentalanine"])
    source.player.go_to_structure(500)
    document = source.export_state()

    shorter = msm.extract(source._molsys, structure_indices=[0, 1, 2],  # noqa: SLF001
                          to_form="molsysmt.MolSys")
    target = _mute(msv.new_view(shorter))

    with pytest.warns(StateStructureIndexOutOfRangeWarning) as caught:
        target.import_state(document)

    assert target.player.index == 0, "the frame was moved somewhere the document did not ask for"
    message = str(caught[0].message)
    assert "500" in message and "3" in message
    assert caught[0].message.code == "MOLSYSVIEWER-STATE-STRUCTURE-INDEX-OUT-OF-RANGE"


def test_save_state_asks_the_frontend_for_the_camera_on_screen(tmp_path):
    """`export_state` reads what it already has; `save_state` refreshes first.

    The difference matters because the frontend debounces: without the request, a save
    made within 300 ms of the last camera move would record the previous view.
    """
    view = _with_camera(_mute(demo["dialanine"]))
    asked = []

    def _request(*args, **kwargs):
        asked.append(True)
        view._last_camera_snapshot = {"position": [9.0, 9.0, 9.0]}  # noqa: SLF001
        return True

    view._request_camera_snapshot = _request  # noqa: SLF001
    destination = tmp_path / "state.json"
    view.save_state(destination)

    assert asked, "save_state wrote the cached camera without asking for a fresh one"
    written = json.loads(destination.read_text(encoding="utf-8"))
    assert written["view"]["camera"] == {"position": [9.0, 9.0, 9.0]}


def test_export_state_never_blocks_on_the_frontend():
    """It runs on every undoable operation; a round trip per checkpoint is unaffordable."""
    view = _with_camera(_mute(demo["dialanine"]))
    asked = []
    view._request_camera_snapshot = lambda *a, **k: asked.append(True)  # noqa: SLF001

    view.export_state()

    assert not asked


def test_undo_restores_the_scene_without_moving_the_camera_or_the_frame():
    """`export_state` serves two masters, and only one of them wants the vantage point.

    A state document records where the user was looking. An undo checkpoint must not:
    undoing an annotation is not consent to have the camera moved and the trajectory
    rewound. This is a regression guard -- when `view` first landed in the document it
    went into the undo snapshots with it.
    """
    view = _with_camera(_mute(demo["pentalanine"]))
    view.player.go_to_structure(100)
    view.annotations.add("site", atom_indices=[0, 1], tag="a1")

    # The user then looks somewhere else and moves along the trajectory.
    view._last_camera_snapshot = {"position": [9.0, 9.0, 9.0]}  # noqa: SLF001
    view.player.go_to_structure(200)

    view.history.undo()

    assert view.annotations.tags() == [], "the annotation was not undone"
    assert view.camera.get_snapshot() == {"position": [9.0, 9.0, 9.0]}
    assert view.player.index == 200


def test_a_camera_move_alone_does_not_make_a_checkpoint_look_like_a_change():
    """The second reason the vantage point stays out of checkpoints.

    Snapshots are compared to skip redundant ones. With the camera inside, a no-op
    operation after any camera move compares unequal and pushes a checkpoint that undoes
    nothing.
    """
    view = _with_camera(_mute(demo["dialanine"]))
    view.annotations.add("site", atom_indices=[0, 1], tag="a1")
    before = view.history._encode(view.history._scene_snapshot())  # noqa: SLF001

    view._last_camera_snapshot = {"position": [7.0, 7.0, 7.0]}  # noqa: SLF001

    assert view.history._encode(view.history._scene_snapshot()) == before  # noqa: SLF001
