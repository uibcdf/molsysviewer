from __future__ import annotations

from molsysviewer import MolSysView
from molsysviewer.demo import demo
import molsysviewer.viewer.regions as viewer_regions


def _fresh_view():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.load(demo["dialanine"]._molsys.copy(), skip_digestion=True)  # noqa: SLF001
    return view


def _dynamic_query_region(view, *, tag: str = "dynamic"):
    region = view._new_region_impl(  # noqa: SLF001
        selection="atom_index < 2",
        tag=tag,
        frame_dependent=True,
        skip_digestion=True,
    )
    region.mode = "dynamic"
    return region


def test_dynamic_region_evaluation_threads_frame_to_molsysmt_select(monkeypatch):
    view = _fresh_view()
    calls: list[object] = []

    def fake_select(_molsys, *, structure_indices=None, **_kwargs):
        calls.append(structure_indices)
        frame = structure_indices[0] if isinstance(structure_indices, list) else 0
        return [int(frame)]

    monkeypatch.setattr(viewer_regions.msm, "select", fake_select)
    region = _dynamic_query_region(view)

    changed = view._evaluate_dynamic_regions_for_frame(3)  # noqa: SLF001

    assert calls[-1] == [3]
    assert changed == [{"tag": region.tag, "atom_indices": [3]}]
    assert region.atom_indices == (3,)


def test_dynamic_region_request_sends_one_runtime_message_for_all_changed_regions(monkeypatch):
    view = _fresh_view()
    sent: list[dict] = []
    view.widget.send = sent.append  # type: ignore[assignment]
    view._ready = True  # noqa: SLF001

    def fake_select(_molsys, *, structure_indices=None, **_kwargs):
        frame = structure_indices[0] if isinstance(structure_indices, list) else 0
        return [int(frame)]

    monkeypatch.setattr(viewer_regions.msm, "select", fake_select)
    _dynamic_query_region(view, tag="a")
    _dynamic_query_region(view, tag="b")

    view._handle_frontend_event({"event": "request_dynamic_region_evaluation", "frame": 4})  # noqa: SLF001

    dynamic_messages = [msg for msg in sent if msg.get("op") == "set_dynamic_region_atoms"]
    assert len(dynamic_messages) == 1
    assert dynamic_messages[0] == {
        "op": "set_dynamic_region_atoms",
        "frame": 4,
        "regions": [
            {"tag": "a", "atom_indices": [4]},
            {"tag": "b", "atom_indices": [4]},
        ],
    }


def test_topological_dynamic_region_is_not_evaluated_per_frame(monkeypatch):
    view = _fresh_view()
    region = view.regions.add(selection="atom_index < 2", tag="topological", skip_digestion=True)
    region.mode = "dynamic"
    assert region.frame_dependent is False

    # A topological dynamic region must not enter the per-frame evaluation set:
    # asserting the output is empty is not enough, since re-evaluating it would
    # coincidentally yield the same atoms. Prove the mechanism directly — it is
    # excluded from the work list AND its recipe is never re-run on frame advance.
    assert region not in view._dynamic_regions_requiring_frame_evaluation()  # noqa: SLF001

    frame_select_calls: list[object] = []
    real_select = viewer_regions.msm.select

    def spy_select(*args, **kwargs):
        frame_select_calls.append(kwargs.get("structure_indices"))
        return real_select(*args, **kwargs)

    monkeypatch.setattr(viewer_regions.msm, "select", spy_select)
    assert view._evaluate_dynamic_regions_for_frame(2) == []  # noqa: SLF001
    assert frame_select_calls == []  # the recipe was never re-run for a frame


def test_dynamic_region_cache_invalidates_on_system_edit(monkeypatch):
    view = _fresh_view()

    def fake_select(_molsys, *, structure_indices=None, **_kwargs):
        frame = structure_indices[0] if isinstance(structure_indices, list) else 0
        return [int(frame)]

    monkeypatch.setattr(viewer_regions.msm, "select", fake_select)
    region = _dynamic_query_region(view)
    view._evaluate_dynamic_regions_for_frame(2)  # noqa: SLF001
    assert (region.uid, 2) in view._dynamic_region_cache  # noqa: SLF001

    view.apply_system_edit(view.molsys)

    assert view._dynamic_region_cache == {}  # noqa: SLF001


def test_over_budget_dynamic_region_freezes_to_static_and_reports_runtime(monkeypatch):
    view = _fresh_view()
    sent: list[dict] = []
    smonitor_events: list[tuple[dict, dict]] = []
    view.widget.send = sent.append  # type: ignore[assignment]
    view._ready = True  # noqa: SLF001
    view._dynamic_region_evaluation_budget_ms = -1.0  # noqa: SLF001

    def fake_select(_molsys, *, structure_indices=None, **_kwargs):
        frame = structure_indices[0] if isinstance(structure_indices, list) else 0
        return [int(frame)]

    monkeypatch.setattr(viewer_regions.msm, "select", fake_select)
    monkeypatch.setattr(
        viewer_regions,
        "emit_from_catalog",
        lambda event, **extra: smonitor_events.append((event, extra)),
    )
    region = _dynamic_query_region(view)

    view._handle_frontend_event({"event": "request_dynamic_region_evaluation", "frame": 5})  # noqa: SLF001

    assert region.mode == "static"
    assert smonitor_events
    assert smonitor_events[0][0] is viewer_regions.CATALOG["dynamic_region_evaluation_over_budget"]
    assert smonitor_events[0][1]["extra"]["tag"] == region.tag
    assert any(msg.get("op") == "dynamic_region_evaluation_warning" for msg in sent)
    assert any(msg.get("op") == "set_dynamic_region_atoms" for msg in sent)


def test_dynamic_region_export_omits_runtime_atom_cache(monkeypatch):
    view = _fresh_view()

    def fake_select(_molsys, *, structure_indices=None, **_kwargs):
        frame = structure_indices[0] if isinstance(structure_indices, list) else 0
        return [int(frame)]

    monkeypatch.setattr(viewer_regions.msm, "select", fake_select)
    region = _dynamic_query_region(view)
    view._evaluate_dynamic_regions_for_frame(3)  # noqa: SLF001
    assert region.atom_indices == (3,)

    state = view.export_state()
    record = next(item for item in state["regions"] if item["tag"] == region.tag)

    assert record["mode"] == "dynamic"
    assert "atom_indices" not in record
