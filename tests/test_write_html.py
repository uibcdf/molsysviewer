import pytest

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import MolSysView


def test_export_html_namespace_delegates(monkeypatch, tmp_path):
    view = MolSysView(debug_js=True)
    called = {}

    def fake_impl(output_filename, **kwargs):
        called["output_filename"] = output_filename
        called["kwargs"] = kwargs

    monkeypatch.setattr(view, "_write_html_impl", fake_impl)

    outfile = tmp_path / "out.html"
    view.export.html(
        str(outfile), title="TestTitle", include_controls=False, include_popout=False, shared_runtime=str(tmp_path)
    )

    assert called["output_filename"] == str(outfile)
    assert called["kwargs"] == {
        "title": "TestTitle",
        "include_controls": False,
        "include_popout": False,
        # Forwarded as given, so the runtime choice is resolved by the
        # implementation and never quietly defaulted in the public wrapper.
        "shared_runtime": str(tmp_path),
        "inline_messages": True,
        # Forwarded as given for the same reason: what the page sits on is
        # resolved by the implementation, not defaulted twice.
        "background": "auto",
    }


def test_studio_html_export_delivers_a_download_reply_without_host_file(tmp_path, monkeypatch):
    from molsysviewer.viewer.panel_actions.viewport import export_html

    from molsysviewer import demo

    monkeypatch.chdir(tmp_path)
    view = demo["dialanine"]
    before = view.export_state()
    transmitted = []
    original_send = view.widget.send

    def observe_send(message, buffers=None):
        transmitted.append(message)
        return original_send(message, buffers=buffers)

    monkeypatch.setattr(view.widget, "send", observe_send)
    export_html(view, {"request_id": "studio-html-review"})
    reply = transmitted[-1]
    assert reply["op"] == "html_export_ready"
    assert reply["request_id"] == "studio-html-review"
    assert reply["filename"] == "molsysviewer.html"
    assert "<!doctype html>" in reply["html"].lower()
    assert 'id="molsysviewer-messages"' in reply["html"]
    assert not list(tmp_path.iterdir())
    assert view.export_state() == before
    with pytest.raises(ValueError, match="request_id"):
        export_html(view, {})
    view.close()
