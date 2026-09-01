"""A session carries its own structure; a state document does not.

Slice 4 of issue #38, and the answer to the question `session_reproducibility.md` has
carried open since Phase 6. That document states the promise plainly -- save, close,
reload elsewhere, continue as if you had never left -- and then lists, as a known gap,
that the structure is not in the document. A state document cannot keep that promise on
its own: reopening one requires the user to already have the right structure loaded, and
to know which one it was.

`save_session` writes both. `load_session` reopens with nothing loaded first, which is
the entire difference and the only reason the format exists.
"""

from __future__ import annotations

import json
import warnings
import zipfile

import molsysmt as msm
import pytest
from molsysviewer._private.smonitor.warnings import StateStructureDiffersWarning
from molsysviewer.demo import demo
from molsysviewer.session import SESSION_VERSION, SessionFormatError

import molsysviewer as msv


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def _saved_session(tmp_path, name="181L"):
    source = _mute(demo[name])
    source.annotations.add("site", atom_indices=[0, 1], tag="a1")
    source.regions.add(selection="atom_name=='CA'", tag="cas")
    source._ready = True  # noqa: SLF001
    source._last_camera_snapshot = {"position": [1.0, 2.0, 3.0]}  # noqa: SLF001
    path = tmp_path / "session.msv"
    source.save_session(path)
    return source, path


def test_a_session_reopens_with_nothing_loaded_first(tmp_path):
    """The whole point. `load_state` cannot do this and is not meant to."""
    source, path = _saved_session(tmp_path)

    restored = _mute(msv.load_session(path))

    assert restored.annotations.tags() == ["a1"]
    assert "cas" in restored.regions.tags()
    assert restored.camera.get_snapshot() == {"position": [1.0, 2.0, 3.0]}
    assert restored.regions.info("cas")["n_atoms"] == source.regions.info("cas")["n_atoms"]


def test_the_reopened_session_does_not_warn_about_its_own_structure(tmp_path):
    """The property the format depends on, and the reason it is `.h5msm`.

    If the structure did not survive the round trip byte-for-byte in the fields the
    fingerprint is taken over, a reopened session would announce that its own structure
    is not the one its own state was written for.
    """
    _, path = _saved_session(tmp_path)

    with warnings.catch_warnings():
        warnings.simplefilter("error", StateStructureDiffersWarning)
        _mute(msv.load_session(path))


def test_a_trajectory_survives_whole_not_only_its_current_frame(tmp_path):
    """Saving one frame would make the saved structure index meaningless."""
    source = _mute(demo["pentalanine"])
    source.player.go_to_structure(500)
    path = tmp_path / "trajectory.msv"
    source.save_session(path)

    restored = _mute(msv.load_session(path))

    n_before = int(msm.get(source._molsys, element="system", n_structures=True))  # noqa: SLF001
    n_after = int(msm.get(restored._molsys, element="system", n_structures=True))  # noqa: SLF001
    assert n_after == n_before == 5000
    assert restored.player.index == 500


def test_saving_a_session_without_a_system_says_so_instead_of_writing_one(tmp_path):
    """A session without a structure is a state document, and `save_state` writes those."""
    view = _mute(msv.MolSysView())
    path = tmp_path / "empty.msv"

    with pytest.raises(ValueError, match="save_state"):
        view.save_session(path)

    assert not path.exists()


def test_a_file_that_is_not_a_session_is_refused_by_name(tmp_path):
    path = tmp_path / "not-a-session.msv"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("something.txt", "hello")

    with pytest.raises(SessionFormatError, match="no manifest"):
        msv.load_session(path)


def test_a_session_from_a_later_build_is_refused_rather_than_half_read(tmp_path):
    _, path = _saved_session(tmp_path)
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(members["manifest.json"])
    manifest["version"] = SESSION_VERSION + 1
    members["manifest.json"] = json.dumps(manifest).encode("utf-8")
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)

    with pytest.raises(SessionFormatError, match="Unsupported session version"):
        msv.load_session(path)


def test_the_manifest_says_what_is_inside_without_parsing_the_scene(tmp_path):
    """A reader -- a person, a tool, a future migration -- should not have to parse the
    scene to learn which structure the file holds."""
    source, path = _saved_session(tmp_path)

    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))

    assert manifest["format"] == "molsysviewer-session"
    assert manifest["structure"]["n_atoms"] == source._molsys.get_n_atoms()  # noqa: SLF001
    assert manifest["structure"]["fingerprint"].startswith("sha256:")


def test_an_archive_that_declares_another_format_is_refused(tmp_path):
    """A zip with a manifest is not thereby a session.

    Distinct from the no-manifest case above: this one looks structurally right and is
    refused on what it says it is, which is the check a neighbouring tool's bundle would
    hit if it happened to be renamed `.msv`.
    """
    path = tmp_path / "other-tool.msv"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps({"format": "some-other-tool", "version": SESSION_VERSION}),
        )

    with pytest.raises(SessionFormatError, match="some-other-tool"):
        msv.load_session(path)
