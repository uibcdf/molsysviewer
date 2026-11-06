"""Real View ownership and the notebook half of the presentation handshake."""

import gc
import weakref

import molsysmt as msm
import numpy as np
import pytest
from ipywidgets.widgets.widget import _instances
from molsysviewer.presentations import _OPEN_PRESENTATIONS

import molsysviewer as msv


def test_preparation_is_headless_independent_and_keeps_native_return_types():
    with msv.demo["pentalanine"] as source:
        service = source.addons.manager.presentations
        handle = service.prepare(
            lambda child: msv.new_view(source.molsys, selection=[0, 1, 2], structure_indices=[2, 0], view=child)
        )
        result = service.get(handle)
        assert isinstance(result, msv.MolSysView)
        assert result.molsys.get_n_atoms() == 3
        assert result.molsys.structures.n_structures == 2
        assert source.molsys.get_n_atoms() == 62
        original = msm.pyunitwizard.get_value(source.molsys.structures.coordinates, to_unit="nm")
        extracted = msm.pyunitwizard.get_value(result.molsys.structures.coordinates, to_unit="nm")
        assert not np.shares_memory(original, extracted)
        np.testing.assert_equal(extracted, original[[2, 0], :3])
        assert service.records()[0]["state"] == "prepared"
        assert service._output is None
        assert handle not in _OPEN_PRESENTATIONS
        assert not source.widget.presentation_host_id
        service.close(handle)
        assert result.closed
        assert service.records() == []


def test_failed_initializer_releases_every_partial_widget():
    with msv.demo["dialanine"] as source:
        baseline = set(_instances)

        def fail(child):
            msv.new_view(source.molsys, view=child)
            raise ValueError("Provider initialization failed")

        with pytest.raises(ValueError, match="Provider initialization failed"):
            source.addons.manager.presentations.prepare(fail)
        assert set(_instances) == baseline
        assert source.addons.manager.presentations.records() == []


def test_browser_ack_and_retry_reuse_result_and_source_close_preserves_it():
    baseline = set(_instances)
    source = msv.demo["dialanine"]
    source_ref = weakref.ref(source)
    service = source.addons.manager.presentations
    handle = service.prepare(lambda child, system=source.molsys: msv.new_view(system, view=child))
    result = service.get(handle)
    source._repr_mimebundle_()
    surface = service._output
    surface._route(surface, {"type": "show", "id": handle, "destination": "window", "request_id": 1}, [])
    assert service.records()[0]["state"] == "opening"
    surface._route(surface, {"type": "shown", "id": handle, "request_id": 0}, [])
    assert service.records()[0]["state"] == "opening"
    surface._route(surface, {"type": "shown", "id": handle, "request_id": 1, "error": "Popup blocked"}, [])
    assert service.get(handle) is result
    assert service.records()[0]["destination"] is None
    surface._route(surface, {"type": "show", "id": handle, "destination": "notebook", "request_id": 2}, [])
    surface._route(surface, {"type": "shown", "id": handle, "request_id": 2}, [])
    assert service.records()[0]["state"] == "shown"
    source.close()
    assert not result.closed
    assert surface.source_closed
    del source
    gc.collect()
    assert source_ref() is None
    assert service.get(handle) is result
    result.close()
    assert handle not in _OPEN_PRESENTATIONS
    assert set(_instances) == baseline


def test_source_closure_discards_unpresented_result_and_refuses_new_work():
    with msv.demo["dialanine"] as source:
        service = source.addons.manager.presentations
        handle = service.prepare(lambda child: msv.new_view(source.molsys, view=child))
        result = service.get(handle)
        source.close()
        assert result.closed
        assert service.records() == []
        with pytest.raises(RuntimeError, match="closed view"):
            service.prepare(lambda child: None)


@pytest.mark.parametrize("destination", [None, "other", [], 42])
def test_invalid_destination_cannot_publish_or_recompute(destination):
    with msv.demo["dialanine"] as source:
        service = source.addons.manager.presentations
        handle = service.prepare(lambda child: None)
        with pytest.raises((ValueError, TypeError)):
            service._show(handle, destination)
        assert service.records()[0]["state"] == "prepared"
