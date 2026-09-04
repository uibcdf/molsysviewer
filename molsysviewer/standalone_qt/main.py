from __future__ import annotations

import argparse
import sys
from typing import Any, Sequence

from ..demo import demo
from .application import launch_remote_qt, launch_standalone_qt0


def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the first MolSysViewer Qt standalone prototype.")
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a molecular system or a demo key when using --demo. If omitted, launch an empty host.",
    )
    parser.add_argument("--demo", action="store_true", help="Interpret source as a MolSysViewer demo key.")
    parser.add_argument(
        "--connect",
        metavar="SESSION_URL",
        help="Open an authenticated remote-session URL in the native Qt shell.",
    )
    parser.add_argument("--output", default=None, help="Output HTML file. Defaults to a temporary file.")
    parser.add_argument("--title", default="MolSysViewer Qt Prototype", help="Window title.")
    parser.add_argument("--selection", default="all", help="Selection passed to new_view(...).")
    parser.add_argument("--structure-indices", default="all", help="Structure indices passed to new_view(...).")
    parser.add_argument("--syntax", default="MolSysMT", help="Selection syntax.")
    parser.add_argument("--load-mode", default="selection", choices=("selection", "all"), help="Load mode.")
    parser.add_argument("--discover-addons", action="store_true", help="Discover known add-ons before launch.")
    parser.add_argument(
        "--addon-module",
        action="append",
        default=[],
        help="Explicit add-on module(s) to register, e.g. molsysviewer_topomt.",
    )
    parser.add_argument("--width", type=int, default=1440, help="Initial window width.")
    parser.add_argument("--height", type=int, default=960, help="Initial window height.")
    parser.add_argument(
        "--no-exec",
        action="store_true",
        help="Build the Qt window and HTML without entering the Qt event loop.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.connect is not None:
        if args.source is not None or args.demo or args.output is not None:
            parser.error("--connect cannot be combined with source, --demo or --output")
        runtime = _get_helper("launch_remote_qt")(
            args.connect,
            title=args.title,
            width=args.width,
            height=args.height,
            exec_app=not args.no_exec,
        )
        print(runtime["session_url"])
        return 0
    source: Any
    if args.source is None:
        source = None
    else:
        source = demo[args.source] if args.demo else args.source

    runtime = _get_helper("launch_standalone_qt0")(
        source,
        output_filename=args.output,
        title=args.title,
        selection=args.selection,
        structure_indices=args.structure_indices,
        syntax=args.syntax,
        load_mode=args.load_mode,
        discover_addons=args.discover_addons,
        addon_modules=args.addon_module,
        width=args.width,
        height=args.height,
        exec_app=not args.no_exec,
    )
    print(runtime["html_path"])
    return 0
