"""Serve a directory of exported views so a browser will render them.

A view that shares a runtime cannot be opened straight from disk: the page and
the runtime beside it are separate opaque origins, and browsers refuse a module
import across one. On a published site the question never arises, because the
site is served — so what is missing is not a mechanism but a server, for the few
minutes between building a documentation site and publishing it.

``python -m molsysviewer.preview docs/_build/html`` is that server.
"""

from __future__ import annotations

import os
from functools import partial
from pathlib import Path

from smonitor import signal

from .._private.arg_digestion import digest


@signal(tags=["tools", "preview", "export"])
@digest()
def preview(
    path: str,
    *,
    port: int = 8000,
    open_browser: bool = True,
    serve_forever: bool = True,
    skip_digestion: bool = False,
):
    """Serve ``path`` over HTTP and open it in a browser.

    Returns the ``http://localhost:<port>/`` URL. With ``serve_forever=True``
    (the default) this blocks until interrupted, which is what a preview is;
    pass ``False`` to get the running server object back and stop it yourself.

    ``port`` is a request, not a promise: if it is taken, the next free one is
    used and the returned URL says which.
    """
    import http.server
    import socketserver
    import threading
    import webbrowser

    root = Path(path)
    if not root.is_dir():
        raise NotADirectoryError(
            f"nothing to preview at {root}: expected a directory of built pages, "
            "for example the output of your documentation build."
        )

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=os.fspath(root))

    class _Server(socketserver.TCPServer):
        allow_reuse_address = True

    # The request log is left on deliberately: a view whose runtime is missing
    # shows up here as a 404 on `viewer.js`, which is the fastest answer there is
    # to "why is the frame empty?".
    server = None
    for candidate_port in range(int(port), int(port) + 20):
        try:
            server = _Server(("127.0.0.1", candidate_port), handler)
            break
        except OSError:
            continue
    if server is None:
        raise OSError(
            f"no free port between {port} and {port + 19}. Pass another `port`."
        )

    url = f"http://localhost:{server.server_address[1]}/"
    print(f"MolSysViewer is serving {root} at {url} (Ctrl-C to stop)")

    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    if not serve_forever:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.shutdown()
        server.server_close()
    return url
