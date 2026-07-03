from __future__ import annotations

import argparse
import html
from pathlib import Path
import tempfile
import webbrowser
from typing import Any, Sequence

from .addons import addons as global_addons
from .demo import demo
from .new_view import new_view
from .viewer import MolSysView


def _empty_host_overlay_html(title: str, demo_links: Sequence[tuple[str, str]] | None = None) -> str:
    demo_names = ", ".join(sorted(demo.keys()))
    escaped_title = html.escape(title)
    escaped_demos = html.escape(demo_names)
    link_items = ""
    if demo_links:
        rendered = []
        for name, href in demo_links:
            rendered.append(
                f'<a class="molsysviewer-standalone0-demo-link" href="{html.escape(href)}">{html.escape(name)}</a>'
            )
        link_items = "\n".join(rendered)
    return f"""
<style>
  #molsysviewer-standalone0-empty {{
    position: fixed;
    inset: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    z-index: 9999;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  #molsysviewer-standalone0-empty .molsysviewer-standalone0-card {{
    max-width: 720px;
    padding: 24px 28px;
    border-radius: 18px;
    background: rgba(18, 24, 33, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.10);
    color: rgba(244, 244, 245, 0.96);
    box-shadow: 0 18px 60px rgba(0, 0, 0, 0.30);
    backdrop-filter: blur(8px);
  }}
  #molsysviewer-standalone0-empty h1 {{
    margin: 0 0 10px;
    font-size: 28px;
    line-height: 1.1;
  }}
  #molsysviewer-standalone0-empty p {{
    margin: 0 0 12px;
    font-size: 14px;
    line-height: 1.5;
    color: rgba(244, 244, 245, 0.82);
  }}
  #molsysviewer-standalone0-empty .molsysviewer-standalone0-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-top: 18px;
  }}
  #molsysviewer-standalone0-empty .molsysviewer-standalone0-tile {{
    padding: 12px 14px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }}
  #molsysviewer-standalone0-empty .molsysviewer-standalone0-label {{
    display: block;
    margin-bottom: 6px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(244, 244, 245, 0.60);
  }}
  #molsysviewer-standalone0-empty .molsysviewer-standalone0-demo-links {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}
  #molsysviewer-standalone0-empty .molsysviewer-standalone0-demo-link {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 7px 10px;
    border-radius: 999px;
    text-decoration: none;
    background: rgba(236, 253, 245, 0.08);
    border: 1px solid rgba(236, 253, 245, 0.14);
    color: rgba(236, 253, 245, 0.96);
    font-size: 12px;
    pointer-events: auto;
  }}
  #molsysviewer-standalone0-empty code {{
    font-size: 12px;
    color: rgba(236, 253, 245, 0.96);
  }}
</style>
<div id="molsysviewer-standalone0-empty">
  <div class="molsysviewer-standalone0-card">
    <h1>{escaped_title}</h1>
    <p>This standalone 0 host is open but no molecular system has been loaded yet.</p>
    <p>Use the host shell to load a demo, file, PDB ID, or MolSysMT source. In CLI/browser-hosted flows you can also start directly with a source.</p>
    <div class="molsysviewer-standalone0-grid">
      <div class="molsysviewer-standalone0-tile">
        <span class="molsysviewer-standalone0-label">App shell</span>
        <code>File → Load Demo / Open File / Load PDB ID</code>
      </div>
      <div class="molsysviewer-standalone0-tile">
        <span class="molsysviewer-standalone0-label">CLI demo</span>
        <code>molsysviewer dialanine --demo</code>
      </div>
      <div class="molsysviewer-standalone0-tile">
        <span class="molsysviewer-standalone0-label">CLI export only</span>
        <code>molsysviewer --no-browser --output /tmp/view.html</code>
      </div>
      <div class="molsysviewer-standalone0-tile">
        <span class="molsysviewer-standalone0-label">Quick demos</span>
        <div class="molsysviewer-standalone0-demo-links">
          {link_items or f"<code>{escaped_demos}</code>"}
        </div>
      </div>
    </div>
  </div>
</div>
"""


def _inject_empty_host_overlay(
    output_path: Path,
    title: str,
    demo_links: Sequence[tuple[str, str]] | None = None,
) -> None:
    text = output_path.read_text(encoding="utf-8")
    overlay = _empty_host_overlay_html(title, demo_links=demo_links)
    if "</body>" in text:
        text = text.replace("</body>", f"{overlay}\n</body>")
    else:
        text = text + overlay
    output_path.write_text(text, encoding="utf-8")


def _build_demo_gallery(
    output_path: Path,
    *,
    selection: str | Sequence[int],
    structure_indices: str | Sequence[int],
    syntax: str,
    load_mode: str,
    include_controls: bool,
    include_popout: bool,
    debug_js: bool | None,
    mode: str,
    runtime_urls: Sequence[str] | None,
    host_event_transport: str | None = None,
    show_empty_host_overlay: bool = True,
) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for demo_name in sorted(demo.keys()):
        demo_path = output_path.with_name(f"{output_path.stem}-demo-{demo_name}.html")
        build_standalone0_html(
            demo[demo_name],
            str(demo_path),
            title=f"MolSysViewer Standalone 0 · {demo_name}",
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            load_mode=load_mode,
            include_controls=include_controls,
            include_popout=include_popout,
            discover_addons=False,
            addon_modules=(),
            apply_project_config=False,
            debug_js=debug_js,
            generate_demo_gallery=False,
            prepare_addons=False,
            mode=mode,
            runtime_urls=runtime_urls,
            host_event_transport=host_event_transport,
            show_empty_host_overlay=show_empty_host_overlay,
        )
        links.append((demo_name, demo_path.name))
    return links


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
        global_addons.discover(include_known_modules=True)

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
    generate_demo_gallery: bool = True,
    prepare_addons: bool = True,
    mode: str = "standalone",
    runtime_urls: Sequence[str] | None = None,
    host_event_transport: str | None = None,
    show_empty_host_overlay: bool = True,
) -> str:
    """Build a first standalone-shaped HTML host using the current viewer runtime."""

    if prepare_addons:
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
    view._write_html_impl(  # noqa: SLF001
        str(output_path),
        title=title,
        include_controls=include_controls,
        include_popout=include_popout,
        mode=mode,
        inline_messages=True,
        runtime_urls=runtime_urls,
        host_event_transport=host_event_transport,
        skip_digestion=True,
    )
    if molecular_system is None and show_empty_host_overlay:
        demo_links = (
            _build_demo_gallery(
                output_path,
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
                load_mode=load_mode,
                include_controls=include_controls,
                include_popout=include_popout,
                debug_js=debug_js,
                mode=mode,
                runtime_urls=runtime_urls,
                host_event_transport=host_event_transport,
                show_empty_host_overlay=show_empty_host_overlay,
            )
            if generate_demo_gallery
            else []
        )
        _inject_empty_host_overlay(output_path, title, demo_links=demo_links)
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
