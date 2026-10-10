"""Owned loopback HTML workspace for headless rendering.

The caller writes HTML into ``directory`` and keeps its output elsewhere.
The context serves that directory plus the supplied runtime without writing
to the package. Exit stops the thread, closes the socket and removes scratch
files on success or failure; cleanup errors remain visible.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Iterator
from urllib.parse import urlsplit


@dataclass(frozen=True)
class HtmlServer:
    directory: Path
    origin: str
    server: HTTPServer
    thread: Thread


@contextmanager
def runtime_html_server(runtime: Path) -> Iterator[HtmlServer]:
    runtime = runtime.resolve(strict=True)
    with TemporaryDirectory(prefix="molsysviewer-image-") as workspace:

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=workspace, **kwargs)

            def translate_path(self, path):
                if urlsplit(path).path == "/viewer.js":
                    return str(runtime)
                return super().translate_path(path)

            def log_message(self, *args):
                pass

        with HTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            thread.start()
            try:
                yield HtmlServer(Path(workspace), f"http://127.0.0.1:{server.server_port}", server, thread)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                if thread.is_alive():
                    raise RuntimeError("Headless HTML server thread did not stop.")
