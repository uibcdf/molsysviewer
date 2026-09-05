"""A self-contained export must render when somebody double-clicks it.

This is the one property of an exported file that cannot be checked by reading
the file: whether a browser, given nothing but that file and no network, boots
the runtime and replays the scene. So it is checked by running a browser.

The failure it guards against is specific and was real. A page that addresses a
runtime beside it — `<script src>` or `await import()` of a sibling file — is
refused when opened from `file://`, because each local file is an opaque origin
and module imports across one are blocked:

    Access to script at 'file:///…/viewer.js' from origin 'null' has been blocked
    by CORS policy

A self-contained export escapes that by carrying the runtime in the page and
making its own blob, which belongs to the page. If anybody ever "simplifies"
that into a sibling file or a CDN URL, this test is what says no.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler
import shutil
from socketserver import TCPServer, ThreadingMixIn
import subprocess
import threading
from collections import Counter
import tempfile
from pathlib import Path

import pytest

from molsysviewer.demo import demo

CHROME = next(
    (
        shutil.which(name)
        for name in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable")
        if shutil.which(name)
    ),
    None,
)

pytestmark = pytest.mark.skipif(
    CHROME is None,
    reason="needs a Chromium-family browser on PATH to open the page for real",
)


def _open_from_disk(html_path: Path) -> tuple[str, str]:
    """Return the page's DOM and console output after opening it as a file."""
    with tempfile.TemporaryDirectory() as profile:
        completed = subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={profile}",
                "--enable-logging=stderr",
                "--v=0",
                "--virtual-time-budget=20000",
                "--dump-dom",
                html_path.resolve().as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
    return completed.stdout, completed.stderr


def test_a_self_contained_export_renders_with_no_server_and_no_network(tmp_path):
    view = demo["dialanine"]
    view.widget.send = lambda *_a, **_k: None  # type: ignore[attr-defined]
    output = tmp_path / "view.html"
    view.export.html(str(output), title="Opened from disk", skip_digestion=True)

    dom, console = _open_from_disk(output)

    assert "blocked by CORS" not in console, (
        "the page tried to reach across an origin it does not have from disk"
    )
    assert 'data-molsysviewer-rendered="true"' in dom, (
        "the runtime never booted; console was:\n" + console[-3000:]
    )
    # Mol* needs a GPU that a headless test machine may not have. That is a
    # limitation of the harness, not of the page, and it happens *after* the
    # runtime booted — which is what this test is about.


def test_the_exported_file_is_the_only_file_needed(tmp_path):
    """No sibling asset, no request. Opening it from an empty directory works."""
    view = demo["dialanine"]
    view.widget.send = lambda *_a, **_k: None  # type: ignore[attr-defined]
    source = tmp_path / "built" / "view.html"
    source.parent.mkdir()
    view.export.html(str(source), skip_digestion=True)

    # Move it somewhere with nothing else in it, the way a file sent by email
    # arrives.
    elsewhere = tmp_path / "downloads"
    elsewhere.mkdir()
    moved = elsewhere / "view.html"
    os.replace(source, moved)
    assert list(elsewhere.iterdir()) == [moved]

    dom, console = _open_from_disk(moved)

    assert 'data-molsysviewer-rendered="true"' in dom, (
        "an export that only works next to its siblings is not self-contained; "
        "console was:\n" + console[-3000:]
    )


def test_the_scene_travels_with_the_page(tmp_path):
    """Rendering proves the runtime loaded; this proves it had something to draw."""
    view = demo["dialanine"]
    view.widget.send = lambda *_a, **_k: None  # type: ignore[attr-defined]
    output = tmp_path / "view.html"
    view.export.html(str(output), skip_digestion=True)

    match = re.search(
        r'<script id="molsysviewer-messages" type="application/json">(.*?)</script>',
        output.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert match is not None
    ops = [message.get("op") for message in json.loads(match.group(1))]

    assert "load_molsys_payload" in ops


# --- the colour the page ends up on -------------------------------------------


@lru_cache(maxsize=1)
def _command_line_chrome_can_load_http() -> str | None:
    """Probe the one thing these three tests need and this machine may not have.

    They read the host document's `data-theme` from inside the iframe, which is a
    same-origin access. `file://` gives every file an opaque origin, so the server is
    not scaffolding that could be dropped -- without it the tests would still pass and
    would be measuring nothing.

    On this machine, `google-chrome --headless` never completes a navigation to
    `http://127.0.0.1`. The server records **no request at all**, so nothing is served
    slowly; the request is never issued. It reproduces with a sixty-byte page, on
    Chrome 149 and on Playwright's Chromium 143 alike, with and without
    `--virtual-time-budget`, and `--timeout` makes it give up and dump an empty
    document rather than fetch one. `file://` is unaffected and Playwright driving the
    same browser over CDP loads the same URL in 0.2 s (uibcdf/molsysviewer#77).

    A canary rather than an xfail: if this returns `None` the browser can do what the
    tests need, and a failure below is then a real one.
    """
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "index.html").write_text("<!doctype html><p id=probe>ok</p>", encoding="utf-8")

        handler = partial(SimpleHTTPRequestHandler, directory=str(root))

        class _Threaded(ThreadingMixIn, TCPServer):
            allow_reuse_address = True
            daemon_threads = True

        server = _Threaded(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            # `ignore_cleanup_errors` because the probe kills Chrome mid-shutdown when
            # it hangs, and a half-written profile is not something to raise about.
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
                try:
                    completed = subprocess.run(
                        [
                            CHROME, "--headless=new", "--no-sandbox",
                            f"--user-data-dir={profile}", "--virtual-time-budget=5000",
                            "--dump-dom", f"http://127.0.0.1:{server.server_address[1]}/index.html",
                        ],
                        capture_output=True, text=True, timeout=40,
                    )
                except subprocess.TimeoutExpired:
                    return "it never finishes a navigation to http://127.0.0.1"
                if "probe" not in completed.stdout:
                    return "it returns an empty document for http://127.0.0.1"
        finally:
            server.shutdown()
            server.server_close()
    return None


needs_http_capable_chrome = pytest.mark.skipif(
    _command_line_chrome_can_load_http() is not None,
    reason=(
        "command-line headless Chrome cannot load http:// on this machine "
        f"({_command_line_chrome_can_load_http()}); these three read the host document "
        "across an iframe, which needs a real origin. See uibcdf/molsysviewer#77."
    ),
)


def _canvas_colour(html_path: Path, host_background: str, host_html: str | None = None) -> tuple:
    """Open the view inside a host page of a given colour, and sample the result.

    Served over HTTP, deliberately. Reading the page around you requires being
    same-origin with it, and two files opened from a disk are two *opaque*
    origins — so from `file://` a view cannot see its host and falls back to the
    reader's preference. Every published site is served, which is the case this
    is about.

    A browser is the only instrument here: what the page sits on is decided at
    read time from the document around it, so no amount of reading the exported
    file can tell you the answer.

    It samples the **background**, deliberately. Whether the molecule finishes
    drawing is not reliable under a software rasteriser — the same page measured
    three times gave 6186, 0 and 6172 lit pixels — so an assertion about the
    molecule would be a flake generator. The colour behind it is stable.
    """
    from PIL import Image

    import molsysviewer as msv

    host = html_path.parent / "host.html"
    host.write_text(
        host_html
        or (
            "<!DOCTYPE html><html data-theme='x'><body style='margin:0;background:"
            f"{host_background}'>"
            f"<iframe src='./{html_path.name}' width='400' height='300' "
            "style='border:none;display:block'></iframe></body></html>"
        ),
        encoding="utf-8",
    )
    shot = html_path.parent / "shot.png"

    server = msv.tools.preview(
        str(html_path.parent), open_browser=False, serve_forever=False, skip_digestion=True
    )
    port = server.server_address[1]
    try:
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run(
                [
                    CHROME, "--headless=new", "--no-sandbox",
                    "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                    f"--user-data-dir={profile}",
                    "--window-size=400,300", "--virtual-time-budget=45000",
                    f"--screenshot={shot}", f"http://127.0.0.1:{port}/host.html",
                ],
                capture_output=True, text=True, timeout=300,
            )
    finally:
        server.shutdown()
        server.server_close()

    if not shot.exists():
        pytest.skip("the browser produced no screenshot")
    image = Image.open(shot).convert("RGB").resize((40, 30))
    return Counter(image.getdata()).most_common(1)[0][0]


def _self_contained(tmp_path: Path) -> Path:
    view = demo["dialanine"]
    view.widget.send = lambda *_a, **_k: None  # type: ignore[attr-defined]
    output = tmp_path / "view.html"
    view.export.html(str(output), skip_digestion=True)
    return output


@needs_http_capable_chrome
def test_an_embedded_view_takes_the_colour_of_the_page_around_it(tmp_path):
    """The site's own theme switch is invisible to every media query.

    It is an attribute on the host's document, and a view served from the same
    site can read it. Copying the host's actual colour is what makes a view stop
    being a bright rectangle on a dark documentation page.
    """
    view = _self_contained(tmp_path)

    assert _canvas_colour(view, "#1a1a1a") == (26, 26, 26), (
        "the view did not take the dark host's background"
    )


@needs_http_capable_chrome
def test_the_same_view_is_light_on_a_light_page(tmp_path):
    """Same file, same reader, different page: the answer comes from the host."""
    view = _self_contained(tmp_path)

    assert _canvas_colour(view, "#ffffff") == (255, 255, 255)


@needs_http_capable_chrome
def test_the_view_matches_the_container_it_was_dropped_into(tmp_path):
    """Not the page's background: the surface immediately behind the frame.

    Reported from MolSysMT's own site. `pydata-sphinx-theme` paints the wrapper
    around a notebook's HTML output in dark mode — `.cell_output .text_html`,
    `#222832`, with padding — over a near-black page. A view that copied the
    *body* sat inside a rectangle a shade lighter than itself, which is the grey
    frame the reader sees, and a transparent one showed that grey instead of the
    page.

    This replicates that structure. The view must come out `#222832`, the colour
    of what is actually behind it, with no help from the site's own CSS.
    """
    view = _self_contained(tmp_path)
    host_html = (
        "<!DOCTYPE html><html data-theme='dark'><head><style>"
        "body { background:#14181f; margin:0 }"
        ".cell_output .text_html { background-color:#222832; border-radius:.25rem; padding:.5rem }"
        "</style></head><body><div class='bd-content'><div class='cell_output'>"
        f"<div class='output text_html'><iframe src='./{tmp_path.name}/../view.html' "
        "width='400' height='300' style='border:none;display:block'></iframe>"
        "</div></div></div></body></html>"
    )
    host_html = host_html.replace(f"./{tmp_path.name}/../view.html", "./view.html")

    assert _canvas_colour(view, "#14181f", host_html=host_html) == (34, 40, 50), (
        "the view took the page's colour instead of the container's"
    )


# --- the scene and the runtime rendering it -----------------------------------


def _with_scene_version(source: Path, version: str, name: str) -> Path:
    """A copy of an exported page claiming a different MolSysViewer made its scene."""
    html = source.read_text(encoding="utf-8")
    patched = re.sub(r'"scene_version":"[^"]*"', f'"scene_version":"{version}"', html, count=1)
    assert patched != html, "the exported page declares no scene version to patch"
    target = source.parent / name
    target.write_text(patched, encoding="utf-8")
    return target


def test_a_scene_from_another_release_says_so(tmp_path):
    """The quietest failure this mechanism can produce, made loud.

    A shared runtime is one file serving every view on a site. Regenerate one
    view after upgrading and that file is replaced for all of them, so the
    untouched pages carry scenes older than the code interpreting them. Nothing
    breaks: the page loads, a molecule appears, and only the reading of the scene
    may have moved.

    Mutation: delete the comparison in `reportSceneRuntimeMismatch` and this must
    go red.
    """
    view = _self_contained(tmp_path)
    stale = _with_scene_version(view, "0.19.0", "stale.html")

    dom, _ = _open_from_disk(stale)

    assert 'data-molsysviewer-version-mismatch="true"' in dom, (
        "a scene from another release rendered without a word"
    )


def test_the_notice_names_both_versions(tmp_path):
    """A warning that does not say which two things disagree cannot be acted on."""
    view = _self_contained(tmp_path)
    stale = _with_scene_version(view, "0.19.0", "stale.html")

    dom, _ = _open_from_disk(stale)
    shown = re.search(r'data-molsysviewer-version-mismatch="true"[^>]*>([^<]*)', dom)

    assert shown is not None
    assert "0.19.0" in shown.group(1), "the notice does not name the scene's version"


def test_a_matching_pair_stays_quiet(tmp_path):
    """The guard has to be silent where it should be, or it trains people to ignore it.

    A development install rebuilds its runtime constantly against an unchanged
    `X.Y.Z`, so the comparison is on the release and not the exact build.
    """
    view = _self_contained(tmp_path)

    dom, _ = _open_from_disk(view)

    assert re.search(
        r'<div[^>]*data-molsysviewer-version-mismatch="true"', dom
    ) is None, "a matching pair produced a mismatch notice"


def test_the_studio_says_it_cannot_act_here(tmp_path):
    """An exported page builds the same Studio a notebook does.

    Every one of its controls asks Python to change the scene and waits for the
    projection back — 127 call sites across ten panels, not one of them local —
    and there is no Python here, so until 2026-08-06 a click did nothing at all
    and said nothing about it.

    Nothing is disabled: the panels still show the scene correctly, and hiding a
    working thing to signal a broken one is its own kind of dishonesty. The panel
    states the situation before anyone clicks, and the seam answers whoever
    clicks anyway.
    """
    view = _self_contained(tmp_path)

    dom, _ = _open_from_disk(view)

    assert 'data-molsysviewer-no-session="true"' in dom, (
        "an exported page offered the Studio with no word about what it cannot do"
    )
    assert "Studio" in dom, "the panels vanished instead of explaining themselves"
