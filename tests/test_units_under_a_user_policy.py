"""Numbers sent or reported without a unit must not depend on the session's unit policy.

Standard units belong to the user's session (the unit-configuration authority,
uibcdf/molsyssuite#18): a user may choose angstrom as the standard length. A value that
leaves the quantity world as a bare number must therefore be converted with an explicit
target unit, never read off a standardized quantity (uibcdf/molsysviewer#96).
"""

import molsysmt as msm
import numpy as np
import pytest
import pyunitwizard as puw

from molsysviewer import MolSysView

ANGSTROM_POLICY = ["angstrom", "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]
BOX_SYSTEM = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]


def _box_edges(view):
    (message,) = [m for m in view._test_message_log if m.get("op") == "add_network_links"]  # noqa: SLF001
    return np.asarray(message["options"]["coordinate_pairs"], dtype=float)


@pytest.fixture
def view_with_box():
    view = MolSysView()
    view.load(BOX_SYSTEM)
    if msm.get(view._molsys, element="system", box=True) is None:  # noqa: SLF001
        pytest.skip("the fixture system carries no box")
    return view


def test_the_box_is_drawn_in_angstrom_whatever_the_standard_length(view_with_box):
    view = view_with_box
    box = msm.get(view._molsys, element="system", box=True)  # noqa: SLF001
    expected = np.asarray(puw.get_value(box, to_unit="angstrom"))[0]
    view.show_box()
    default_edges = _box_edges(view)

    view._test_message_log.clear()  # noqa: SLF001
    with puw.context(standard_units=ANGSTROM_POLICY):
        # The policy is really in force: MolSysMT now answers in angstrom.
        assert str(puw.get_unit(msm.get(view._molsys, element="system", box=True))) == "angstrom"  # noqa: SLF001
        view.show_box()
        policy_edges = _box_edges(view)

    assert np.allclose(policy_edges, default_edges)
    # The first edge runs from the origin along the box vector a, which must be a in Å.
    assert np.allclose(default_edges[0][1] - default_edges[0][0], expected[0])


def test_a_world_offset_is_reported_in_the_unit_the_api_accepts():
    view = MolSysView()
    view.load(BOX_SYSTEM)
    view.annotations.add_annotation("x", atom_indices=[0], offset_mode="world", offset=[0.2, 0.0, 0.0])

    def reported():
        info = view.annotations.info()
        info = info if isinstance(info, list) else [info]
        return info[0]["offset"]

    assert reported() == pytest.approx([0.2, 0.0, 0.0])  # nm, as add_annotation reads it
    with puw.context(standard_units=ANGSTROM_POLICY):
        assert reported() == pytest.approx([0.2, 0.0, 0.0])
