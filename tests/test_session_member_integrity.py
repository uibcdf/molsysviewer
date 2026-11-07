"""Session members stay contained and unambiguous before molecular loading."""

import json
import stat
import zipfile
from copy import deepcopy

import pytest
from ipywidgets.widgets.widget import _instances
from molsysviewer.session import SessionFormatError

import molsysviewer as msv


@pytest.fixture(scope="module")
def session_inputs(tmp_path_factory):
    directory = tmp_path_factory.mktemp("private-session-inputs")
    fixtures = {}
    with msv.demo["dialanine"] as small, msv.demo["pentalanine"] as full:
        with full.extract(structure_indices=[0, 8, 3]) as large:
            for name, view in (("small", small), ("large", large)):
                path = directory / f"{name}.msv"
                view.save_session(path)
                with zipfile.ZipFile(path) as archive:
                    fixtures[name] = {key: archive.read(key) for key in archive.namelist()}
    return fixtures


def write_archive(path, members, extra=()):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        for name, data in extra:
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr(name, data)


def reject_preserving_destination(path, reuse):
    with msv.demo["dialanine"] as destination:
        destination.regions.add([0, 1], tag="keep")
        destination.annotations.add("keep", atom_indices=[0], tag="keep-note")
        destination.annotations.add("redo", atom_indices=[1], tag="redo-note")
        destination.history.undo()
        handles = (destination.regions["keep"], destination.annotations.get("keep-note"))
        system = destination.molsys
        state = deepcopy(destination.export_state())
        history = (list(destination.history._undo), list(destination.history._redo))
        messages = deepcopy(destination._test_message_log)
        widgets = set(_instances)
        restored = None
        try:
            with pytest.raises(SessionFormatError):
                restored = msv.load_session(path, view=destination if reuse else None)
        finally:
            if restored is not None and not reuse:
                restored.close()
        assert destination.molsys is system
        assert destination.export_state() == state
        assert destination.regions["keep"] is handles[0]
        assert destination.annotations.get("keep-note") is handles[1]
        assert (destination.history._undo, destination.history._redo) == history
        assert destination._test_message_log == messages
        assert set(_instances) == widgets


@pytest.mark.parametrize("reuse", [False, True])
def test_declared_external_member_cannot_replace_embedded_bytes(tmp_path, session_inputs, reuse):
    external = tmp_path / "controlled-external.h5msm"
    external.write_bytes(session_inputs["large"]["structure.h5msm"])
    members = dict(session_inputs["large"])
    declaration = json.loads(members["manifest.json"])
    declaration["structure"]["member"] = str(external)
    members["manifest.json"] = json.dumps(declaration).encode()
    members["structure.h5msm"] = session_inputs["small"]["structure.h5msm"]
    members[str(external)] = session_inputs["small"]["structure.h5msm"]
    path = tmp_path / "controlled.msv"
    write_archive(path, members)
    reject_preserving_destination(path, reuse)
    assert external.read_bytes() == session_inputs["large"]["structure.h5msm"]


@pytest.mark.parametrize("reuse", [False, True])
@pytest.mark.parametrize(
    "name",
    [
        "../system.h5msm",
        "./system.h5msm",
        "/system.h5msm",
        "C:/system.h5msm",
        "C:system.h5msm",
        "folder\\system.h5msm",
        "folder//system.h5msm",
        "folder/../system.h5msm",
    ],
)
def test_nonportable_declared_members_reject_before_destination_changes(tmp_path, session_inputs, reuse, name):
    members = dict(session_inputs["small"])
    declaration = json.loads(members["manifest.json"])
    declaration["structure"]["member"] = name
    members["manifest.json"] = json.dumps(declaration).encode()
    members[name] = members["structure.h5msm"]
    path = tmp_path / "nonportable.msv"
    write_archive(path, members)
    reject_preserving_destination(path, reuse)


@pytest.mark.parametrize("name", ["structure.h5msm", "data/system snapshot.h5msm", "datos/estructura-α.h5msm"])
@pytest.mark.parametrize("reuse", [False, True])
def test_portable_selected_members_retain_exact_scientific_content(tmp_path, session_inputs, name, reuse):
    members = dict(session_inputs["small"])
    declaration = json.loads(members["manifest.json"])
    declaration["structure"]["member"] = name
    members["manifest.json"] = json.dumps(declaration).encode()
    members[name] = members["structure.h5msm"]
    path = tmp_path / "portable.msv"
    write_archive(path, members)
    with msv.demo["pentalanine"] as destination:
        widgets = set(_instances)
        restored = msv.load_session(path, view=destination if reuse else None)
        try:
            assert restored.molsys.get_n_atoms() == 22
            assert (
                restored.export_state()["sources"]["binding"] == json.loads(members["state.json"])["sources"]["binding"]
            )
            assert set(_instances) == widgets if reuse else len(set(_instances) - widgets) == 2
        finally:
            if not reuse:
                restored.close()


@pytest.mark.parametrize("member", ["manifest.json", "state.json", "structure.h5msm"])
@pytest.mark.parametrize("reuse", [False, True])
def test_duplicate_required_members_are_ambiguous(tmp_path, session_inputs, member, reuse):
    path = tmp_path / "duplicate.msv"
    members = session_inputs["small"]
    write_archive(path, members, [(member, members[member])])
    reject_preserving_destination(path, reuse)


@pytest.mark.parametrize(
    "damage",
    [
        "manifest_list",
        "manifest_version_bool",
        "structure_list",
        "member_integer",
        "state_list",
        "state_bad_json",
        "state_bad_utf8",
    ],
)
def test_malformed_header_documents_raise_format_errors(tmp_path, session_inputs, damage):
    members = dict(session_inputs["small"])
    declaration = json.loads(members["manifest.json"])
    if damage == "manifest_list":
        declaration = []
    elif damage == "manifest_version_bool":
        declaration["version"] = True
    elif damage == "structure_list":
        declaration["structure"] = ["wrong"]
    elif damage == "member_integer":
        declaration["structure"]["member"] = 10
    elif damage == "state_list":
        members["state.json"] = b"[]"
    elif damage == "state_bad_json":
        members["state.json"] = b"{"
    else:
        members["state.json"] = b"\xff"
    members["manifest.json"] = json.dumps(declaration).encode()
    path = tmp_path / "header.msv"
    write_archive(path, members)
    reject_preserving_destination(path, True)


@pytest.mark.parametrize("mode", [stat.S_IFDIR, stat.S_IFLNK])
def test_required_structure_must_be_a_regular_archive_entry(tmp_path, session_inputs, mode):
    path = tmp_path / "entry-type.msv"
    members = session_inputs["small"]
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            if name == "structure.h5msm":
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (mode | 0o600) << 16
                archive.writestr(info, data)
            else:
                archive.writestr(name, data)
    reject_preserving_destination(path, True)
