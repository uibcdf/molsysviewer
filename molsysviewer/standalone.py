from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
import webbrowser
from typing import Any, Sequence

from .addons import addons as global_addons
from .demo import demo
from .new_view import new_view
from .viewer import MolSysView


def _resolve_view(
    molecular_system: Any,
    *,
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    debug_js: bool | None = None,
) -> MolSysView:
    if molecular_system is None:
        return MolSysView(debug_js=debug_js)
    if isinstance(molecular_system, MolSysView):
        return molecular_system
    return new_view(
        molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        debug_js=debug_js,
    )


def _prepare_addons(
    *,
    discover_addons: bool = False,
    addon_modules: Sequence[str] | None = None,
    apply_project_config: bool = True,
) -> None:
    if apply_project_config:
        project_config = Path("_molsysviewer.py")
        if project_config.exists():
            global_addons.load_project_config(str(project_config))

    if discover_addons:
        global_addons.discover()

    for module_name in addon_modules or ():
        global_addons.register_module(module_name)


def build_standalone0_html(
    molecular_system: Any,
    output_filename: str,
    *,
    title: str = "MolSysViewer Standalone 0",
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    include_controls: bool = True,
    include_popout: bool = False,
    discover_addons: bool = False,
    addon_modules: Sequence[str] | None = None,
    apply_project_config: bool = True,
    debug_js: bool | None = None,
) -> str:
    """Build a first standalone-shaped HTML host using the current viewer runtime."""

    _prepare_addons(
        discover_addons=discover_addons,
        addon_modules=addon_modules,
        apply_project_config=apply_project_config,
    )
    view = _resolve_view(
        molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        debug_js=debug_js,
    )
    output_path = Path(output_filename).expanduser().resolve()
    view.export.html(
        str(output_path),
        title=title,
        include_controls=include_controls,
        include_popout=include_popout,
        mode="standalone",
    )
    return str(output_path)


def launch_standalone0(
    molecular_system: Any,
    output_filename: str | None = None,
    *,
    open_browser: bool = True,
    title: str = "MolSysViewer Standalone 0",
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    include_controls: bool = True,
    include_popout: bool = False,
    discover_addons: bool = False,
    addon_modules: Sequence[str] | None = None,
    apply_project_config: bool = True,
    debug_js: bool | None = None,
) -> str:
    """Create a standalone-0 HTML file and optionally open it in the browser."""

    if output_filename is None:
        with tempfile.NamedTemporaryFile(prefix="molsysviewer-standalone0-", suffix=".html", delete=False) as handle:
            output_filename = handle.name

    path = build_standalone0_html(
        molecular_system,
        output_filename,
        title=title,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        include_controls=include_controls,
        include_popout=include_popout,
        discover_addons=discover_addons,
        addon_modules=addon_modules,
        apply_project_config=apply_project_config,
        debug_js=debug_js,
    )
    if open_browser:
        webbrowser.open_new_tab(Path(path).as_uri())
    return path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a minimal MolSysViewer standalone 0 HTML host.")
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a molecular system or a demo key when using --demo. If omitted, launch an empty host.",
    )
    parser.add_argument("--demo", action="store_true", help="Interpret source as a MolSysViewer demo key.")
    parser.add_argument("--output", default=None, help="Output HTML file. Defaults to a temporary file.")
    parser.add_argument("--title", default="MolSysViewer Standalone 0", help="Standalone HTML title.")
    parser.add_argument("--selection", default="all", help="Selection passed to new_view(...).")
    parser.add_argument("--structure-indices", default="all", help="Structure indices passed to new_view(...).")
    parser.add_argument("--syntax", default="MolSysMT", help="Selection syntax.")
    parser.add_argument("--load-mode", default="selection", choices=("selection", "all"), help="Load mode.")
    parser.add_argument("--no-browser", action="store_true", help="Create the HTML without opening it.")
    parser.add_argument("--discover-addons", action="store_true", help="Discover known add-ons before launch.")
    parser.add_argument(
        "--addon-module",
        action="append",
        default=[],
        help="Explicit add-on module(s) to register, e.g. molsysviewer_topomt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    source: Any
    if args.source is None:
        source = None
    else:
        source = demo[args.source] if args.demo else args.source
    path = launch_standalone0(
        source,
        output_filename=args.output,
        open_browser=not args.no_browser,
        title=args.title,
        selection=args.selection,
        structure_indices=args.structure_indices,
        syntax=args.syntax,
        load_mode=args.load_mode,
        discover_addons=args.discover_addons,
        addon_modules=args.addon_module,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
