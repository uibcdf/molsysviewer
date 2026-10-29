"""Factory contracts on actual molecular systems and viewer owners."""

import pytest
from molsysviewer._private.exceptions import ArgumentError

import molsysviewer as msv


@pytest.fixture
def source():
    with msv.demo["dialanine"] as view:
        yield view.molsys


def test_new_view_selection_mode_loads_selection(source):
    with msv.new_view(source, selection=[0, 1], load_mode="selection") as view:
        assert view.whole.get(n_atoms=True) == 2
        assert view.regions.tags() == []
        assert view.whole.visible


def test_new_view_all_mode_loads_all_and_creates_selection_region(source):
    with msv.new_view(source, selection=[0, 1], load_mode="all") as view:
        assert view.whole.get(n_atoms=True) == source.get_n_atoms()
        assert view.regions["selection"].atom_indices == (0, 1)
        assert not view.whole.visible
        assert view.regions["selection"].representation == "inherit"


def test_new_view_all_mode_warns_and_keeps_whole_visible_for_empty_selection(source):
    with msv.new_view() as view:
        with pytest.warns(UserWarning, match="resolved to zero atoms"):
            assert msv.new_view(source, selection="atom_index<0", load_mode="all", view=view) is view
        assert view.whole.visible
        assert view.regions.tags() == []
        assert view.whole.get(n_atoms=True) == source.get_n_atoms()


def test_new_view_all_mode_inherits_whole_preset(source):
    with msv.new_view(source, selection="group_index==0", load_mode="all") as view:
        region = view.regions["selection"]
        assert region.representation == "inherit"
        assert region.provenance["kind"] == "query"


def test_new_view_forwards_syntax_to_load_and_region(source):
    with msv.new_view(source, selection="resid 0", syntax="MDTraj", load_mode="all") as view:
        assert view.regions["selection"].atom_indices == tuple(view.whole.select("resid 0", syntax="MDTraj"))


def test_new_view_refuses_invalid_selection_before_hiding_whole(source):
    with msv.new_view() as view:
        with pytest.raises(Exception):
            msv.new_view(source, selection="this is not a valid query!", load_mode="all", view=view)
        assert view.whole.visible
        assert not view.regions


def test_new_view_rejects_invalid_load_mode(source):
    with pytest.raises(ArgumentError):
        msv.new_view(source, load_mode="invalid")


@pytest.mark.parametrize("load_mode,n_atoms,regions", [("selection", 2, []), ("all", 22, ["selection"])])
def test_host_replacement_uses_factory_loading_policy(source, load_mode, n_atoms, regions):
    from molsysviewer.new_view import _load_initial_system

    with msv.new_view(source) as view:
        view.regions.add([5], tag="old")
        _load_initial_system(view, source, selection=[0, 1], load_mode=load_mode, replace=True)
        assert view.whole.get(n_atoms=True) == n_atoms
        assert view.regions.tags() == regions
        assert view.whole.visible == (load_mode == "selection")


def test_host_replacement_rejects_invalid_visual_selection_before_replacing(source):
    from molsysviewer.new_view import _load_initial_system

    with msv.new_view(source, selection=[0, 1]) as view:
        before = view.molsys
        with pytest.raises(Exception):
            _load_initial_system(view, source, selection="invalid query!", load_mode="all", replace=True)
        assert view.molsys is before
        assert view.whole.get(n_atoms=True) == 2


def test_host_empty_visual_selection_keeps_full_system_visible(source):
    from molsysviewer.new_view import _load_initial_system

    with msv.new_view() as view:
        with pytest.warns(UserWarning, match="resolved to zero atoms"):
            _load_initial_system(view, source, selection="atom_index<0", load_mode="all", replace=True)
        assert view.whole.get(n_atoms=True) == 22
        assert view.whole.visible
        assert view.regions.tags() == []
