"""Initial widget intent survives a deferred molecular-data handshake (#247)."""

import molsysviewer as msv


def test_prepared_molecular_view_and_explicit_reset_publish_initial_intent():
    source = msv.demo["dialanine"]
    view = msv.MolSysView()
    try:
        assert view.widget.has_molecular_system is False
        view.load(source.molsys)
        assert view._ready is False
        assert view.widget.initial_messages == []
        assert view.widget.get_state()["has_molecular_system"] is True

        view.reset_viewer()
        assert view.widget.has_molecular_system is False

        view.load(source.molsys)
        assert view.widget.has_molecular_system is True
    finally:
        view.close()
        source.close()
