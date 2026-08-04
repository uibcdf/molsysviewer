"""The preview server: the answer to "why is my embed blank?" before publishing.

A view that shares a runtime has to be served, so between building a site and
publishing it there is a gap where the author cannot see their own work. This
closes it, and these tests pin the two things an author would notice: that it
serves the files, and that it says so when there is nothing to serve.
"""

from __future__ import annotations

import urllib.error
import urllib.request

import pytest

import molsysviewer as msv


def _served(directory, **kwargs):
    server = msv.tools.preview(
        str(directory), open_browser=False, serve_forever=False, skip_digestion=True, **kwargs
    )
    port = server.server_address[1]
    return server, f"http://127.0.0.1:{port}"


def test_preview_serves_the_directory(tmp_path):
    (tmp_path / "view.html").write_text("<h1>a scene</h1>", encoding="utf-8")
    (tmp_path / "viewer.js").write_text("// runtime", encoding="utf-8")

    server, base = _served(tmp_path)
    try:
        assert urllib.request.urlopen(f"{base}/view.html").read() == b"<h1>a scene</h1>"
        # The runtime beside it is the whole reason a server is needed at all.
        assert urllib.request.urlopen(f"{base}/viewer.js").read() == b"// runtime"
    finally:
        server.shutdown()
        server.server_close()


def test_preview_refuses_a_directory_that_is_not_there(tmp_path):
    """Naming the wrong directory must not look like a working empty site."""
    with pytest.raises(NotADirectoryError):
        msv.tools.preview(str(tmp_path / "built"), open_browser=False, skip_digestion=True)


def test_preview_moves_on_when_the_port_is_taken(tmp_path):
    """Two previews at once is normal — comparing two builds, for instance."""
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")

    first, first_url = _served(tmp_path, port=8931)
    try:
        second, second_url = _served(tmp_path, port=8931)
        try:
            assert second_url != first_url, "the second preview reused a busy port"
            assert urllib.request.urlopen(f"{second_url}/index.html").read() == b"ok"
        finally:
            second.shutdown()
            second.server_close()
    finally:
        first.shutdown()
        first.server_close()


@pytest.mark.parametrize("bad_port", [80, 0, "8000", True])
def test_preview_rejects_a_port_it_could_not_bind(tmp_path, bad_port):
    from molsysviewer._private.exceptions import ArgumentError

    with pytest.raises(ArgumentError):
        msv.tools.preview(str(tmp_path), port=bad_port, open_browser=False)
