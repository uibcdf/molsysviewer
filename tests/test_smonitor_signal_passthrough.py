from __future__ import annotations

import smonitor

from molsysviewer import MolSysView, pyunitwizard as puw


def test_smonitor_signal_preserves_shape_fluent_api_when_enabled():
    smonitor.configure(enabled=True, profiling=True, profiling_sample_rate=1.0)
    view = MolSysView()

    shape = view.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(1.0, "nm"),
        tag="site",
        skip_digestion=True,
    )
    result = shape.set_color(0x123456)

    assert result is None
    assert view.shapes["site"] is shape
    assert view._shape_history[-1]["options"]["color"] == 0x123456  # noqa: SLF001


def test_smonitor_signal_preserves_region_fluent_api_when_disabled():
    smonitor.configure(enabled=False)
    view = MolSysView()

    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", skip_digestion=True)
    result = region.set_representation("line", skip_digestion=True)

    assert result is None
    assert view.regions["frag"] is region
    assert region.representation == "line"
