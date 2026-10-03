"""Studio routes explicit loading intentions through real public scientific input."""
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def sources(tmp_path):
    source = msm.extract(msv.demo["pentalanine"].molsys, selection=list(range(10)),
                         structure_indices=[0, 8, 3], to_form="molsysmt.MolSys")
    msm.set(source, time=None, box=None)
    paths = []
    for index in range(4):
        item = msm.copy(source)
        msm.set(item, coordinates=puw.quantity(puw.get_value(item.structures.coordinates, to_unit="nm") + index, "nm"))
        path = tmp_path / f"source-{index}.h5msm"
        msm.h5msm.write(item, str(path))
        paths.append(str(path))
    return paths


def _view():
    view = msv.new_view(debug_js=True)
    view._ready = True
    sent = []
    view.widget.send = sent.append
    return view, sent


def _request(source, **kwargs):
    return {"action": "load_systems", "request_id": "request-1", "molecular_system": source,
            "mode": "add", "multiple": False, "structure_indices": [0], **kwargs}


def test_batch_and_progressive_panel_paths_have_equivalent_science_and_regions(sources):
    batch, sent = _view()
    dispatch_panel_action(batch, _request(sources, multiple=True, labels=["A", "A", "C", "D"]))
    assert sent[-1] == {"op": "system_load_result", "request_id": "request-1", "ok": True,
                        "n_atoms": 40, "n_structures": 1, "n_sources": 4}
    progressive, _ = _view()
    for index, source in enumerate(sources):
        dispatch_panel_action(progressive, _request(source, label=["A", "A", "C", "D"][index]))
        assert len(progressive.regions) == (0 if index == 0 else index + 1)
    np.testing.assert_array_equal(puw.get_value(batch.get_coordinates(), to_unit="nm"),
                                  puw.get_value(progressive.get_coordinates(), to_unit="nm"))
    assert len(batch.load_blocks) == len(batch.regions) == 4
    assert [record["label"] for record in batch.load_blocks] == ["A", "A", "C", "D"]


def test_panel_frame_selectors_and_pairing_preserve_order(sources):
    view, _ = _view()
    dispatch_panel_action(view, _request(sources[:2], multiple=True, structure_pairing="by_index",
                                        selection=[[0, 2], [1, 3]], structure_indices=[[2, 0], [1, 2]]))
    assert view.molsys.get_n_atoms() == 4 and view.player.n_structures == 2
    assert view.load_blocks[0]["structure_map"]["runs"] == [[2, 0, 1], [0, 1, 1]]
    assert view.load_blocks[1]["structure_map"]["runs"] == [[1, 0, 2]]


def test_replace_and_append_are_explicit_scientific_operations(sources):
    view, sent = _view()
    dispatch_panel_action(view, _request(sources[:2], multiple=True))
    dispatch_panel_action(view, _request(sources[2], mode="replace"))
    assert view.molsys.get_n_atoms() == 10 and len(view.load_blocks) == 1 and len(view.regions) == 0
    dispatch_panel_action(view, _request(sources[2], mode="append_structures", structure_indices=[1, 2]))
    assert view.player.n_structures == 3
    assert sent[-1]["n_sources"] == 1


def test_complementary_amber_files_remain_one_system():
    files = [str(msm.systems["pentalanine"]["pentalanine.prmtop"]),
             str(msm.systems["pentalanine"]["pentalanine.inpcrd"])]
    view, sent = _view()
    dispatch_panel_action(view, _request(files, multiple=False, label="complementary", selection=list(range(10))))
    assert view.molsys.get_n_atoms() == 10 and len(view.load_blocks) == 1 and not view.regions
    assert sent[-1]["n_sources"] == 1


@pytest.mark.parametrize("kwargs", [
    {"multiple": "true"}, {"mode": "auto"}, {"mode": "unknown"},
    {"molecular_system": []}, {"molecular_system": [None]}, {"molecular_system": 1},
    {"request_id": ""}, {"structure_indices": [True]}, {"structure_indices": [0.5]},
    {"multiple": True, "structure_indices": "all"},
    {"multiple": True, "mode": "append_structures"},
    {"multiple": True, "labels": ["too few"]},
])
def test_rejected_studio_intent_reports_failure_and_preserves_the_active_scene(sources, kwargs):
    view, sent = _view()
    dispatch_panel_action(view, _request(sources[0]))
    before, system = deepcopy(view.export_state()), view.molsys
    old_messages = list(view._test_message_log)
    with pytest.raises(Exception):
        dispatch_panel_action(view, _request(sources[1:3], **kwargs))
    assert view.molsys is system and view.export_state() == before
    # Runtime acknowledgments never enter the molecular/scene replay journal.
    assert view._test_message_log == old_messages
    assert sent[-1]["op"] == "system_load_result" and sent[-1]["ok"] is False


@pytest.mark.parametrize("selection", ["all", [0, 1]])
@pytest.mark.parametrize("structure_indices", ["all", [0], [2, 0]])
def test_partial_h5msm_domains_follow_provider_composition(sources, tmp_path, selection, structure_indices):
    """Compose only through the provider; unsupported versions preserve the view."""
    from molsysmt._private.smonitor.exceptions import MultipleMolecularSystemsError

    source = msm.convert(str(sources[0]), to_form="molsysmt.MolSys")
    topology = str(tmp_path / "topology.h5msm")
    structures = str(tmp_path / "structures.h5msm")
    msm.h5msm.write_layers(topology, topology=source.topology)
    msm.h5msm.write_layers(structures, structures=source.structures)
    view = msv.new_view(msv.demo["dialanine"].molsys, structure_indices=[0])
    original = view.molsys
    original_state = view.export_state()
    try:
        try:
            expected = msm.convert([topology, structures], to_form="molsysmt.MolSys",
                                   selection=selection, structure_indices=structure_indices)
        except MultipleMolecularSystemsError:
            with pytest.raises(MultipleMolecularSystemsError):
                view.load([topology, structures], selection=selection,
                          structure_indices=structure_indices, mode="replace")
            assert view.molsys is original
            assert view.export_state() == original_state
        else:
            view.load([topology, structures], selection=selection,
                      structure_indices=structure_indices, mode="replace")
            np.testing.assert_array_equal(puw.get_value(view.get_coordinates(), to_unit="nm"),
                                          puw.get_value(expected.structures.coordinates, to_unit="nm"))
            assert view.molsys.get_n_atoms() == expected.get_n_atoms()
            assert len(view.load_blocks) == 1 and len(view.regions) == 0
    finally:
        view.close()


def test_later_missing_file_cannot_partially_load_a_batch(sources):
    view, sent = _view()
    dispatch_panel_action(view, _request(sources[0]))
    before, system = deepcopy(view.export_state()), view.molsys
    with pytest.raises(Exception):
        dispatch_panel_action(view, _request([sources[1], sources[2] + ".missing"], multiple=True))
    assert view.molsys is system and view.export_state() == before
    assert sent[-1]["ok"] is False


def test_real_frontend_event_reports_failure_and_allows_a_later_retry(sources):
    view, sent = _view()
    bad = _request(sources[:2], multiple=True, labels=["bad"])
    view._handle_frontend_event({"event": "interaction_context_action", **bad})
    assert view.molsys is None
    assert any(message.get("op") == "system_load_result" and not message["ok"] for message in sent)
    assert sent[-1]["op"] == "backend_error_occurred"
    good = _request(sources[:2], multiple=True, labels=["A", "B"], request_id="retry")
    view._handle_frontend_event({"event": "interaction_context_action", **good})
    assert view.molsys.get_n_atoms() == 20 and sent[-1]["ok"] is True
