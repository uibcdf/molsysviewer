from __future__ import annotations

from molsysviewer import MolSysView
from molsysviewer.demo import demo


def _fresh_view():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.load(demo["dialanine"]._molsys.copy(), skip_digestion=True)  # noqa: SLF001
    view._ready = True  # noqa: SLF001
    return view


def test_region_order_context_actions_dispatch_to_real_methods():
    view = _fresh_view()
    first = view.regions.add(atom_indices=[0, 1], tag="first", representation="line", skip_digestion=True)
    second = view.regions.add(atom_indices=[1, 2], tag="second", representation="line", skip_digestion=True)
    assert first.order < second.order

    view._handle_frontend_event(  # noqa: SLF001
        {"event": "interaction_context_action", "action": "raise_region_to_front", "tag": "first"}
    )
    assert first.order > second.order

    view._handle_frontend_event(  # noqa: SLF001
        {"event": "interaction_context_action", "action": "send_region_to_back", "tag": "first"}
    )
    assert first.order < second.order


def test_region_details_payload_includes_provenance_mode_order_and_broken_flag():
    view = _fresh_view()
    sent: list[dict] = []
    view.widget.send = sent.append  # type: ignore[assignment]
    region = view.regions.add(selection="atom_index < 2", tag="query", skip_digestion=True)
    region.mode = "dynamic"

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "get_region_details",
            "tag": "query",
            "request_id": 7,
        }
    )

    details = next(msg for msg in sent if msg.get("op") == "region_details")
    assert details["request_id"] == 7
    assert details["tag"] == "query"
    assert details["mode"] == "dynamic"
    assert details["order"] == region.order
    assert details["broken"] is False
    assert details["provenance"]["kind"] == "query"
    assert details["provenance"]["expression"] == "atom_index < 2"


def test_compose_regions_context_action_accepts_variadic_operands():
    view = _fresh_view()
    view.regions.add(atom_indices=[0, 1, 2, 3], tag="base", skip_digestion=True)
    view.regions.add(atom_indices=[1], tag="one", skip_digestion=True)
    view.regions.add(atom_indices=[3], tag="three", skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "compose_regions",
            "tag_a": "base",
            "operand_tags": ["one", "three"],
            "op": "difference",
            "new_tag": "remaining",
        }
    )

    assert tuple(view.regions["remaining"].atom_indices) == (0, 2)


def test_make_regions_by_context_action_can_split_active_selection():
    view = _fresh_view()
    view.active_selection.set([0, 1], skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "make_regions_by",
            "element": "group",
            "selection": "active",
        }
    )

    assert view.regions.count() > 0
