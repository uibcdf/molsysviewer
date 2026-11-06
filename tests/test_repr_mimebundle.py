from molsysviewer import MolSysView


def test_repr_mimebundle_uses_one_real_presentation_surface_for_the_source_widget():
    with MolSysView(debug_js=True) as view:
        service = view.addons.manager.presentations
        assert service._output is None
        first, metadata = view._repr_mimebundle_(include={"text/plain"}, exclude={"text/html"})
        surface = service._output
        assert surface.source_id == view.widget.model_id
        assert surface.runtime_entrypoint == "presentationSurface"
        assert first["application/vnd.jupyter.widget-view+json"]["model_id"] == surface.model_id
        assert metadata == {}
        again, _ = view._repr_mimebundle_()
        assert again["application/vnd.jupyter.widget-view+json"]["model_id"] == surface.model_id
        assert service.records() == []
    assert surface.comm is None and view.widget.comm is None
