from __future__ import annotations

import molsysmt as msm
import pytest

from molsysviewer import MolSysView, demo, tools


def test_tools_basic_concatenate_structures_returns_new_view_from_views():
    view_a = demo["dialanine"]
    view_b = demo["dialanine"]

    result = tools.basic.concatenate_structures([view_a, view_b], debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view_a
    assert result is not view_b
    assert msm.get(result._molsys, element="system", n_structures=True, skip_digestion=True) == 2  # noqa: SLF001
    assert result.atom_mask is not None
    assert len(result.atom_mask) == msm.get(result._molsys, element="system", n_atoms=True, skip_digestion=True)  # noqa: SLF001


def test_tools_basic_concatenate_structures_accepts_molecular_systems():
    molsys_a = demo["dialanine"]._molsys  # noqa: SLF001
    molsys_b = demo["dialanine"]._molsys  # noqa: SLF001

    result = tools.concatenate_structures([molsys_a, molsys_b], debug_js=True)

    assert isinstance(result, MolSysView)
    assert msm.get(result._molsys, element="system", n_structures=True, skip_digestion=True) == 2  # noqa: SLF001


def test_tools_basic_query_wrappers_operate_on_view():
    view = demo["dialanine"]

    assert tools.select(view, selection=[0, 1, 2]) == [0, 1, 2]
    assert tools.get(view, element="system", n_atoms=True) == 22
    assert tools.contains(view, peptides=True) is True
    assert tools.is_composed_of(view, n_molecules=1) is True

    info = tools.info(view, element="group", selection=[0])
    assert hasattr(info, "data")
    assert info.data.shape[0] == 1


def test_tools_basic_extract_returns_subset_view():
    view = demo["dialanine"]

    result = tools.extract(view, selection=[0, 1, 2], debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view
    assert msm.get(result._molsys, element="system", n_atoms=True, skip_digestion=True) == 3  # noqa: SLF001


def test_tools_basic_live_edit_wrappers_delegate_to_view(monkeypatch):
    monkeypatch.setenv("NUMBA_CACHE_DIR", "/tmp/numba_cache")

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    tools.set(view, element="group", selection=[0], group_name="ACE2")
    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["payload"]["atoms"]["residue_name"][:5] == ["ACE2"] * 5

    tools.append_structures(view, demo["dialanine"]._molsys)
    assert msm.get(view._molsys, element="system", n_structures=True, skip_digestion=True) == 2  # noqa: SLF001

    tools.remove(view, selection=[0])
    assert msm.get(view._molsys, element="system", n_atoms=True, skip_digestion=True) == 21  # noqa: SLF001


def test_tools_basic_add_wrapper_delegates_to_view(monkeypatch):
    monkeypatch.setenv("NUMBA_CACHE_DIR", "/tmp/numba_cache")

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    tools.add(view, demo["dialanine"]._molsys)

    assert msm.get(view._molsys, element="system", n_atoms=True, skip_digestion=True) == 44  # noqa: SLF001
