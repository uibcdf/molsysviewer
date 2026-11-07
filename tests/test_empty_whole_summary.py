"""Empty metadata avoids invalid scientific calls without losing scene content (#323)."""

from __future__ import annotations

import inspect
import json
import re
import sys
from contextlib import contextmanager
from copy import deepcopy

import molsysmt as msm
import pytest
from molsysviewer._pyunitwizard import puw
from molsysviewer.standalone import build_standalone0_html

import molsysviewer as msv

EMPTY_CONTAINS = dict.fromkeys(
    ("protein", "peptide", "nucleic_dna", "nucleic_rna", "small_molecule", "lipid", "ion", "water"), 0
)


@contextmanager
def _observe_form_calls():
    """Observe real get_form calls, forwarding and restoring a caller's profiler."""
    previous = sys.getprofile()
    if previous is not None and not callable(previous):
        pytest.skip("The real-call probe cannot compose this noncallable native profiler.")
    code = inspect.unwrap(msm.get_form).__code__
    observed = {"calls": 0, "none": []}

    def observe(frame, event, arg):
        if previous is not None:
            previous(frame, event, arg)
        if event == "call" and frame.f_code is code:
            observed["calls"] += 1
            if frame.f_locals["molecular_system"] is None:
                caller = frame.f_back
                observed["none"].append((caller.f_code.co_filename, caller.f_lineno, caller.f_code.co_name))

    try:
        sys.setprofile(observe)
        yield observed
    finally:
        sys.setprofile(previous)


def _html_messages(path):
    match = re.search(
        r'<script id="molsysviewer-messages" type="application/json">(.*?)</script>',
        path.read_text(),
        re.DOTALL,
    )
    assert match, "the standalone page must carry its actual scene projection"
    return json.loads(match.group(1))


def _whole(messages):
    return next(message for message in messages if message["op"] == "set_whole_summary")


@pytest.mark.parametrize("with_shape", [False, True], ids=["empty", "absolute-shape-only"])
def test_empty_popup_and_standalone_summaries_preserve_scene_without_invalid_form_probes(tmp_path, with_shape):
    with msv.MolSysView() as view:
        if with_shape:
            view.shapes.add_sphere(center=puw.quantity([1, 2, 3], "nm"), radius="0.2 nm", tag="absolute-site")
        before = deepcopy(view.export_state())
        with _observe_form_calls() as observed:
            panel = view.build_popup_scene_snapshot("panel")
            canvas = view.build_popup_scene_snapshot("canvas")
            filename = tmp_path / "scene.html"
            build_standalone0_html(
                view,
                str(filename),
                prepare_addons=False,
                generate_demo_gallery=False,
                apply_project_config=False,
            )
        assert observed["none"] == []
        exported = _html_messages(filename)
        for messages in (panel, canvas, exported):
            assert _whole(messages)["contains"] == EMPTY_CONTAINS
            assert _whole(messages)["composition"] == {}
        assert view.molsys is None, "metadata must not prepare a hidden molecular system"
        assert view.export_state() == before
        if with_shape:
            canvas_shapes = [message for message in canvas if message["op"] == "add_sphere"]
            assert [message for message in exported if message["op"] == "add_sphere"] == canvas_shapes
            assert len(canvas_shapes) == 1
            assert canvas_shapes[0]["options"]["tag"] == "absolute-site"
            assert canvas_shapes[0]["options"]["center"] == [10.0, 20.0, 30.0]
            assert canvas_shapes[0]["options"]["radius"] == 2.0
            assert len(before["shapes"]) == 1


def test_empty_standalone_bootstrap_does_not_probe_none_as_a_molecular_system(tmp_path):
    filename = tmp_path / "empty.html"
    with _observe_form_calls() as observed:
        build_standalone0_html(
            None,
            str(filename),
            prepare_addons=False,
            generate_demo_gallery=False,
            apply_project_config=False,
        )
    assert observed["none"] == []
    assert _whole(_html_messages(filename))["contains"] == EMPTY_CONTAINS


def test_loaded_pentalanine_summary_retains_nonzero_native_composition():
    with msv.demo["pentalanine"] as view:
        with _observe_form_calls() as observed:
            summary = view._whole_summary_record()
        assert observed["calls"] > 0, "the loaded control must reach the genuine form owner"
        assert observed["none"] == []
        assert summary["composition"] == {"atoms": 62, "groups": 7, "chains": 1, "molecules": 1, "entities": 1}
        assert summary["contains"] == {**EMPTY_CONTAINS, "peptide": 1}
        assert msm.get(view.molsys, element="system", output_type="values", n_peptides=True) == 1


def test_call_observer_forwards_and_restores_the_preexisting_profiler_after_failure():
    original = sys.getprofile()
    if original is not None and not callable(original):
        pytest.skip("The observer must leave this noncallable native profiler untouched.")
    calls = []

    def sentinel():
        return None

    def previous(frame, event, arg):
        if original is not None:
            original(frame, event, arg)
        if event == "call" and frame.f_code is sentinel.__code__:
            calls.append("sentinel")

    sys.setprofile(previous)
    try:
        with pytest.raises(RuntimeError, match="controlled probe failure"):
            with _observe_form_calls():
                sentinel()
                raise RuntimeError("controlled probe failure")
        assert sys.getprofile() is previous
        assert calls == ["sentinel"]
    finally:
        sys.setprofile(original)
