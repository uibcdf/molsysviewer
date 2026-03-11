from __future__ import annotations

import molsysmt as msm

from molsysviewer import MolSysView, demo, tools


def test_tools_basic_merge_views_merges_scene_state_and_resolves_tag_collisions():
    view_a = demo["dialanine"]
    view_b = demo["dialanine"]

    view_a.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view_b.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view_a.whole.set_representation("cartoon", skip_digestion=True)
    view_a.whole.hide(skip_digestion=True)
    region_a = view_a.new_region(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)
    region_a.hide(skip_digestion=True)
    pocket_a = view_a.shapes.add_pocket_surface(atom_indices=[0, 1, 2], tag="pocket", skip_digestion=True)
    pocket_a.hide(skip_digestion=True)
    view_a.hide(selection=[2], skip_digestion=True)

    view_b.new_region(atom_indices=[0, 1], tag="frag", representation="line", skip_digestion=True)
    analysis_b = view_b.new_layer(tag="analysis", kind="annotation", owner="b", skip_digestion=True)
    analysis_b.hide(skip_digestion=True)
    pocket_b = view_b.shapes.add_links(atom_pairs=[[0, 1]], tag="pocket", skip_digestion=True)
    pocket_b.hide(skip_digestion=True)
    view_b.hide(selection=[0], skip_digestion=True)

    result = tools.basic.merge_views([view_a, view_b], debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view_a
    assert result is not view_b
    assert msm.get(result._molsys, element="system", n_atoms=True, skip_digestion=True) == 44  # noqa: SLF001
    assert getattr(result.whole, "_representation", None) == "cartoon"
    assert result._global_hidden is True  # noqa: SLF001

    assert set(result.regions) == {"frag", "frag__2"}
    assert result.regions["frag"].atom_indices == (0, 1, 2)
    assert result.regions["frag__2"].atom_indices == (22, 23)
    assert result.regions["frag"]._hidden is True  # noqa: SLF001

    assert set(result.layers) == {"pocket", "analysis", "pocket__2"}
    assert result.layers["pocket"]._hidden is True  # noqa: SLF001
    assert result.layers["analysis"]._hidden is True  # noqa: SLF001
    assert result.layers["pocket__2"]._hidden is True  # noqa: SLF001

    ops = [msg.get("op") for msg in result._message_history]  # noqa: SLF001
    assert ops[0] == "load_molsys_payload"
    assert "set_global_representation" in ops
    assert "hide_global" in ops

    region_b_msg = next(
        msg for msg in result._message_history if msg.get("op") == "create_region" and msg.get("tag") == "frag__2"  # noqa: SLF001
    )
    assert region_b_msg["atom_indices"] == [22, 23]

    links_msg = next(
        msg
        for msg in result._message_history  # noqa: SLF001
        if msg.get("op") == "add_network_links" and msg.get("options", {}).get("tag") == "pocket__2"
    )
    assert links_msg["options"]["atom_pairs"] == [[22, 23]]

    visibility_msg = next(msg for msg in reversed(result._message_history) if msg.get("op") == "update_visibility")  # noqa: SLF001
    assert visibility_msg["options"]["visible_atom_indices"] == [
        0,
        1,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
    ]
