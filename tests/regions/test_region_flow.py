from __future__ import annotations

from importlib.resources import files

import molsysmt as msm  # noqa: F401
import molsysviewer as viewer


def test_demo_region_hide():
    """Smoke-test: create a region and hide it without errors."""

    demo_system = files("molsysviewer.data.h5msm").joinpath("1TCD.h5msm")
    view = viewer.new_view(demo_system, debug_js=True)
    # Avoid real frontend traffic; we only need the calls to not fail.
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.show()
    region = view.new_region("chain_id == 'A'", representation="sticks")
    region.hide()

    assert region is not None
    assert region.tag in view.regions
