from molsysviewer import MolSysView


def test_repr_mimebundle_delegates_to_widget(monkeypatch):
    view = MolSysView(debug_js=True)
    called = {}

    def fake_repr_mimebundle(*, include=None, exclude=None):
        called["include"] = include
        called["exclude"] = exclude
        return ({"text/plain": "ok"}, {})

    monkeypatch.setattr(view.widget, "_repr_mimebundle_", fake_repr_mimebundle)

    result = view._repr_mimebundle_(include={"text/plain"}, exclude={"text/html"})

    assert result == ({"text/plain": "ok"}, {})
    assert called == {"include": {"text/plain"}, "exclude": {"text/html"}}
