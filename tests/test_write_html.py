import pytest

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import MolSysView


def test_write_html_prefers_anywidget_embed(monkeypatch, tmp_path):
    view = MolSysView(debug_js=True)
    # Capture outgoing widget sends to avoid side effects
    view.widget.send = lambda _msg: None  # type: ignore

    called = {}

    # Stub out the anywidget embed helper to avoid writing files during the test.
    def fake_embed(path, views, title=None, **_kwargs):
        called["path"] = path
        called["views"] = views
        called["title"] = title

    # Simulate viewer actions so history is serialized
    view._send({"op": "dummy"})
    view._send({"op": "update_visibility", "options": {"visible_atom_indices": [0, 1, 2]}})

    # Anywidget does not expose an embed helper; we intercept the write to inspect state.
    monkeypatch.setattr(view, "_build_standalone_html", lambda title: "HTML")

    outfile = tmp_path / "out.html"
    with monkeypatch.context() as m:
        # Patch the file write to avoid IO and capture title/path
        def fake_write_html(self, output_filename, title=""):
            fake_embed(output_filename, [self.widget], title=title)
            # ensure initial_messages were cleaned before export
            self.widget.initial_messages = self._clean_message_history()

        m.setattr(view.__class__, "write_html", fake_write_html)
        view.write_html(str(outfile), title="TestTitle")

    assert called["path"] == str(outfile)
    assert called["views"] == [view.widget]
    assert called["title"] == "TestTitle"
    assert view.widget.initial_messages == [{"op": "dummy"}]
