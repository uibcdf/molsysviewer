"""Non-inline public HTML exports must carry the complete canonical scene."""

import json
import re
from copy import deepcopy
from urllib.parse import unquote

import pytest
from molsysviewer.demo import demo

import molsysviewer as msv


def _block(path, name):
    match = re.search(rf'<script id="{name}" type="application/json">(.*?)</script>', path.read_text(), re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_noninline_shared_export_preserves_scene_in_a_versioned_sidecar(tmp_path):
    with demo["pentalanine"] as source, msv.new_view(source.molsys, structure_indices=[0, 8, 3]) as view:
        view.annotations.add("Saved label", atom_indices=[0], tag="label")
        view.regions.add(atom_indices=[0, 1], tag="region").hide()
        view.player.go_to_structure(2)
        state = deepcopy(view.export_state())
        output = tmp_path / "view #1 %.html"
        expected = view._build_export_messages()
        view.export.html(str(output), shared_runtime=str(tmp_path), inline_messages=False)
        ui = _block(output, "molsysviewer-ui")
        assert "#" not in ui["messages_url"]
        assert " " not in ui["messages_url"]
        sidecar = tmp_path / unquote(ui["messages_url"])
        data = json.loads(sidecar.read_text())
        assert data["format"] == "molsysviewer-messages" and data["version"] == 1
        assert data["messages"] == expected
        assert _block(output, "molsysviewer-messages") == []
        assert view.export_state() == state


def test_noninline_export_updates_its_own_sidecar(tmp_path):
    with demo["dialanine"] as view:
        output = tmp_path / "view.html"
        view.export.html(str(output), shared_runtime=str(tmp_path), inline_messages=False)
        view.annotations.add("New label", atom_indices=[0], tag="new-label")
        view.export.html(str(output), shared_runtime=str(tmp_path), inline_messages=False)
        data = json.loads((tmp_path / "view.html.messages.json").read_text())
        assert any(message.get("tag") == "new-label" for message in data["messages"])


@pytest.mark.parametrize("unrelated", ['{"user_data":true}', "[]", "not JSON"])
def test_noninline_export_preserves_unrelated_sidecar_and_existing_html(tmp_path, unrelated):
    with demo["dialanine"] as view:
        output = tmp_path / "view.html"
        output.write_text("Existing page")
        sidecar = tmp_path / "view.html.messages.json"
        sidecar.write_text(unrelated)
        with pytest.raises(FileExistsError, match="unrelated scene data"):
            view.export.html(str(output), shared_runtime=str(tmp_path), inline_messages=False)
        assert output.read_text() == "Existing page"
        assert sidecar.read_text() == unrelated


def test_self_contained_export_keeps_scene_inline_even_when_flag_is_false(tmp_path):
    with demo["dialanine"] as view:
        output = tmp_path / "view.html"
        view.export.html(str(output), inline_messages=False)
        assert "messages_url" not in _block(output, "molsysviewer-ui")
        assert _block(output, "molsysviewer-messages")[0]["op"] == "load_molsys_payload"
        assert list(tmp_path.iterdir()) == [output]
