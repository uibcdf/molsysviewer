"""Pre-1.0 scale guard: a load big enough to kill the tab must say so.

1.0 materializes every selected structure on purpose — windowed residency would
change what `view.molsys` means and is post-1.0. What 1.0 owes the user is an
honest ceiling: numbers, a way forward, and never a silent death.
"""

import warnings

import pytest

import molsysviewer as msv
from molsysviewer._private import scale_budget
from molsysviewer._private.scale_budget import (
    StructureScaleWarning,
    check_structure_scale,
    coordinate_bytes,
    suggested_structure_stride,
)

MB = 1024 * 1024


def test_coordinate_bytes_scales_with_both_axes():
    # float32 x/y/z per atom per structure.
    assert coordinate_bytes(1, 1) == 12
    assert coordinate_bytes(100_000, 100) == 100_000 * 100 * 12
    # The measured villin case: 120 MB.
    assert coordinate_bytes(100_000, 100) / MB == pytest.approx(114.4, abs=0.5)


def test_a_load_within_budget_is_silent():
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any warning fails the test
        assert check_structure_scale(62, 5000, budget_bytes=256 * MB) is None


def test_a_load_over_budget_warns_with_numbers_and_a_way_forward():
    with pytest.warns(StructureScaleWarning) as record:
        total = check_structure_scale(100_000, 1000, budget_bytes=256 * MB)
    assert total == coordinate_bytes(100_000, 1000)
    message = str(record[0].message)
    # The user must learn what it costs...
    assert "1000 structures" in message and "100000 atoms" in message
    # ...that a popup makes it worse...
    assert "popup" in message
    # ...and exactly how to proceed, not just that it is big.
    assert "structure_indices=range(0, 1000," in message
    assert "set_structure_scale_budget" in message


def test_the_guard_warns_and_never_refuses():
    # Returning a value rather than raising is the contract: only the caller
    # knows whether their machine can hold it.
    with pytest.warns(StructureScaleWarning):
        assert isinstance(check_structure_scale(100_000, 1000, budget_bytes=1), int)


def test_the_suggested_stride_actually_brings_it_under_budget():
    n_atoms, n_structures, budget = 100_000, 1000, 256 * MB
    stride = suggested_structure_stride(n_atoms, n_structures, budget)
    assert stride > 1
    kept = -(-n_structures // stride)
    assert coordinate_bytes(n_atoms, kept) <= budget


def test_a_selection_within_budget_needs_no_stride():
    assert suggested_structure_stride(62, 5000, 256 * MB) == 1


@pytest.mark.parametrize("n_atoms, n_structures", [(0, 10), (10, 0), (-1, 5)])
def test_degenerate_dimensions_are_ignored(n_atoms, n_structures):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert check_structure_scale(n_atoms, n_structures) is None


def test_the_budget_is_publicly_configurable_and_can_be_silenced():
    original = scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES
    try:
        # Lowering it makes the guard speak sooner...
        msv.config.set_structure_scale_budget(1)
        with pytest.warns(StructureScaleWarning):
            check_structure_scale(62, 5000, budget_bytes=scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES)
        # ...and zero silences it entirely, for a machine that can hold anything.
        msv.config.set_structure_scale_budget(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert check_structure_scale(
                100_000, 10_000, budget_bytes=scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES
            ) is None
    finally:
        scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES = original


@pytest.mark.parametrize("bad", [-1, 1.5, True, "256"])
def test_the_public_setter_rejects_nonsense(bad):
    with pytest.raises(ValueError):
        msv.config.set_structure_scale_budget(bad)


def test_a_real_load_within_budget_does_not_warn():
    import molsysmt as msm

    view = msv.MolSysView()
    with warnings.catch_warnings():
        warnings.simplefilter("error", StructureScaleWarning)
        view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    assert view.molsys.get_n_atoms() > 0


def test_a_real_load_over_a_lowered_budget_warns():
    import molsysmt as msm

    original = scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES
    try:
        msv.config.set_structure_scale_budget(1024)  # 1 KB: anything real exceeds it
        view = msv.MolSysView()
        with pytest.warns(StructureScaleWarning):
            view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    finally:
        scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES = original
