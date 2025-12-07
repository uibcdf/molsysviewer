from __future__ import annotations

import molsysmt as msm  # noqa: F401
import molsysviewer as viewer


def test_demo_region_hide():
    """Smoke-test: crear región y ocultarla sin errores."""

    view = viewer.demo.tctim(debug_js=True)
    # Evitar tráfico real con el frontend; solo necesitamos que no falle.
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.show()
    region = view.new_region("chain_id == 'A'", representation="sticks")
    region.hide()

    assert region is not None
    assert region.tag in view.regions
