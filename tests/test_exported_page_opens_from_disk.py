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

Every test here opens the page from a **file**, with the Chromium-family browser
the reader happens to have installed. That is the question this file asks, and
it is why the browser is not pinned.

Three colour tests used to live here and no longer do. They embed the export in
a host page and check that it copies the surface behind it, which means reading
`window.parent.document` across the iframe -- a same-origin access that `file://`
cannot give, so they needed a server. Command-line headless Chrome never
completes a navigation to `http://127.0.0.1` on the development machine
(uibcdf/molsysviewer#77), so they skipped permanently, and a test that skips
permanently checks nothing. They are
`molsysviewer/js/tests/e2e/exported-page-colour.e2e.ts` now, where Playwright
drives the same browser family over CDP and loads the same URL in 0.2 s
(uibcdf/molsysviewer#81).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
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


def _self_contained(tmp_path: Path) -> Path:
    view = demo["dialanine"]
    view.widget.send = lambda *_a, **_k: None  # type: ignore[attr-defined]
    output = tmp_path / "view.html"
    view.export.html(str(output), skip_digestion=True)
    return output


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
