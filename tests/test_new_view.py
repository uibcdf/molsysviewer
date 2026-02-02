from __future__ import annotations

import pytest

from molsysviewer.new_view import new_view
from molsysviewer._private.exceptions import ArgumentError


class DummyWhole:
    def __init__(self) -> None:
        self.hidden = False
        self._preset = None
        self._representation = None
        self._repr_params = {}

    def hide(self) -> None:
        self.hidden = True


class DummyRegion:
    def __init__(self) -> None:
        self.repr_calls: list[dict] = []

    def set_representation(self, representation=None, *, preset=None, **params) -> None:
        self.repr_calls.append(
            {"representation": representation, "preset": preset, "params": params}
        )


class DummyView:
    def __init__(self) -> None:
        self.whole = DummyWhole()
        self.load_calls: list[dict] = []
        self.new_region_calls: list[dict] = []
        self.region = DummyRegion()

    def load(self, molecular_system, *, selection="all", structure_indices="all", syntax="MolSysMT", skip_digestion=False, **_kwargs) -> None:
        self.load_calls.append(
            {
                "molecular_system": molecular_system,
                "selection": selection,
                "structure_indices": structure_indices,
                "syntax": syntax,
                "skip_digestion": skip_digestion,
            }
        )

    def new_region(self, selection, *, tag=None, syntax="MolSysMT", skip_digestion=False, **_kwargs):
        self.new_region_calls.append({"selection": selection, "tag": tag, "syntax": syntax, "skip_digestion": skip_digestion})
        return self.region


def test_new_view_selection_mode_loads_selection():
    view = DummyView()
    result = new_view(
        "system",
        selection="molecule_index == 0",
        load_mode="selection",
        view=view,
    )

    assert result is view
    assert view.load_calls == [
        {
            "molecular_system": "system",
            "selection": "molecule_index == 0",
            "structure_indices": "all",
            "syntax": "MolSysMT",
            "skip_digestion": True,
        }
    ]
    assert view.new_region_calls == []
    assert view.whole.hidden is False


def test_new_view_all_mode_loads_all_and_creates_selection_region():
    view = DummyView()
    result = new_view(
        "system",
        selection="molecule_index == 0",
        load_mode="all",
        view=view,
    )

    assert result is view
    assert view.whole.hidden is True
    assert view.load_calls == [
        {
            "molecular_system": "system",
            "selection": "all",
            "structure_indices": "all",
            "syntax": "MolSysMT",
            "skip_digestion": True,
        }
    ]
    assert view.new_region_calls == [
        {"selection": "molecule_index == 0", "tag": "selection", "syntax": "MolSysMT", "skip_digestion": True}
    ]
    assert view.region.repr_calls == [
        {"representation": None, "preset": "auto", "params": {"skip_digestion": True}}
    ]


def test_new_view_all_mode_inherits_whole_preset():
    view = DummyView()
    view.whole._preset = "polymer-cartoon"
    view.whole._repr_params = {"quality": "high"}

    new_view(
        "system",
        selection="molecule_index == 0",
        load_mode="all",
        view=view,
    )

    assert view.region.repr_calls == [
        {
            "representation": None,
            "preset": "polymer-cartoon",
            "params": {"quality": "high", "skip_digestion": True},
        }
    ]


def test_new_view_forwards_syntax_to_load_and_region():
    view = DummyView()

    new_view(
        "system",
        selection="resid 1",
        load_mode="all",
        syntax="MDTraj",
        view=view,
    )

    assert view.load_calls[0]["syntax"] == "MDTraj"
    assert view.load_calls[0]["skip_digestion"] is True
    assert view.new_region_calls[0]["syntax"] == "MDTraj"
    assert view.new_region_calls[0]["skip_digestion"] is True


def test_new_view_rejects_invalid_load_mode():
    view = DummyView()
    with pytest.raises(ArgumentError):
        new_view("system", load_mode="invalid", view=view)
