"""Public control-area preferences survive validation, copy and HTML export."""
import json
import re
import warnings

import pytest
from molsysviewer._private.exceptions import ArgumentError

import molsysviewer as msv


@pytest.fixture
def view():
    value = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
    yield value
    value.close()


def test_default_reveal_area_and_public_normalization(view):
    assert view.widget.autohide_scope == "controls"
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        view.set_controls_visible(True, autohide=True, autohide_scope=" CANVAS ", position="top-left")
    assert view.widget.autohide_scope == "canvas"
    assert view.widget.controls_position == ["top", "left"]
    assert not [r for r in records if type(r.message).__name__ == "DigestNotDigestedWarning"]
    view.set_controls_visible(False, autohide_scope="controls")
    assert not view.widget.show_controls
    view.set_controls_visible(True, autohide=False)
    assert not view.widget.autohide_controls
    assert view.widget.autohide_scope == "controls"


@pytest.mark.parametrize("value", ["corner", "off", True, ["canvas"]])
def test_bad_scope_is_rejected_before_mutation(view, value):
    before = (view.widget.show_controls, view.widget.autohide_scope)
    with pytest.raises(ArgumentError):
        view.set_controls_visible(False, autohide_scope=value)
    assert (view.widget.show_controls, view.widget.autohide_scope) == before


def test_configured_scope_is_used_for_a_new_native_view():
    before = msv.config.autohide_scope
    try:
        msv.config.autohide_scope = "canvas"
        with_view = msv.new_view(msv.demo["dialanine"].molsys)
        try:
            assert with_view.widget.autohide_scope == "canvas"
        finally:
            with_view.close()
    finally:
        msv.config.autohide_scope = before


def test_scope_survives_copy_and_self_contained_export(view, tmp_path):
    view.set_controls_visible(True, autohide=True, autohide_scope="canvas")
    copied = msv.tools.copy(view)
    try:
        assert copied.widget.autohide_scope == "canvas"
    finally:
        copied.close()
    output = tmp_path / "controls.html"
    view.export.html(str(output), include_popout=False)
    ui = re.search(r'<script id="molsysviewer-ui" type="application/json">(.*?)</script>', output.read_text(), re.S)
    assert ui is not None
    assert json.loads(ui.group(1))["autohide_scope"] == "canvas"
