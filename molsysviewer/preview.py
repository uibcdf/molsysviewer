"""Command line for :func:`molsysviewer.tools.preview`.

    python -m molsysviewer.preview docs/_build/html

It lives here rather than inside `molsysviewer.tools` because that package
imports its submodules, and `python -m` on an already-imported module runs it
twice and says so. The function is the API; this is only the way to type it.
"""

from __future__ import annotations

import argparse

from .tools.preview import preview


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m molsysviewer.preview",
        description="Serve a directory of exported views so a browser will render them.",
    )
    parser.add_argument("path", help="directory to serve, e.g. docs/_build/html")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser")
    args = parser.parse_args(argv)

    preview(args.path, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":  # pragma: no cover - exercised by hand
    main()
