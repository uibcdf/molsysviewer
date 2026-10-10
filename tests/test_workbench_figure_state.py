"""The configured workbench PNG recipe survives state/session restoration (#227)."""

from copy import deepcopy

import pytest

import molsysviewer as msv
from molsysviewer import FigureSpec


@pytest.fixture
def view():
    with msv.demo["dialanine"] as scene:
        yield scene


@pytest.mark.parametrize("scale", [True, float("nan"), float("inf"), float("-inf")])
def test_figure_owner_rejects_nonfinite_or_boolean_scale(scale):
    with pytest.raises(ValueError, match="finite positive"):
        FigureSpec(scale=scale)


@pytest.mark.parametrize("session", [False, True])
def test_workbench_recipe_survives_file_roundtrip(view, tmp_path, session):
    view.set_figure_spec(FigureSpec(scale=1.5, background="transparent", preset="publication-dark"))
    expected = dict(view._current_figure_spec)
    path = tmp_path / ("review.msv" if session else "review.json")
    (view.save_session if session else view.save_state)(path)
    view.set_figure_spec(FigureSpec(scale=4, background="white"))
    if session:
        assert msv.load_session(path, view=view) is view
    else:
        view.load_state(path)
    assert view._current_figure_spec == expected
    assert view.export_state()["figure"] == {"scale": 1.5, "background": "transparent", "preset": "publication-dark"}


@pytest.mark.parametrize(
    "record",
    [
        [],
        {},
        {"scale": 2, "preset": "publication-light", "background": False},
        *[
            {"scale": scale, "preset": "publication-light", "background": "white"}
            for scale in (True, 0, -1, float("nan"), float("inf"), "2")
        ],
    ],
)
def test_invalid_recipe_does_not_mutate_work(view, record):
    view.annotations.add("keep", atom_indices=[0], tag="keep")
    view.set_figure_spec(FigureSpec(scale=3))
    before = view.export_state()
    invalid = deepcopy(before)
    invalid["figure"] = record
    with pytest.raises((ValueError, TypeError)):
        view.import_state(invalid)
    assert view.export_state() == before
    assert view.history.can_undo()


def test_legacy_state_and_explicit_reset_keep_existing_contracts(view):
    legacy = view.export_state()
    assert "figure" not in legacy
    view.set_figure_spec(FigureSpec(scale=1.5))
    view.import_state(legacy)
    assert view._current_figure_spec["figure_scale"] == 1.5
    view.reset_viewer()
    assert view._current_figure_spec is None
