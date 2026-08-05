"""Where an exported lite view finds its runtime.

The governing decision is reproducibility over freshness: an exported page must
keep rendering what it rendered, offline, without depending on a registry entry
surviving. See
`devguide/pending_proposals/embedding_views_in_external_documentation.md` and the
defect it closes, `devguide/pending_bugs/docs_lite_views_pinned_to_unpublished_npm_version.md`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import molsysviewer as msv
from molsysviewer._private.runtime_asset import (
    RUNTIME_ASSET_MARKER,
    RUNTIME_ASSET_NAME,
    is_release_version,
    place_runtime_asset,
    runtime_asset_source,
)
from molsysviewer.demo import demo


def _view():
    view = demo["dialanine"]
    view.widget.send = lambda *_args, **_kwargs: None  # type: ignore[attr-defined]
    return view


def _runtime_candidates(html_path: Path) -> list[str]:
    html = html_path.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="molsysviewer-runtime-candidates" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None, "the exported page declares no runtime candidates"
    return json.loads(match.group(1))


def _embedded_runtime(html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="molsysviewer-runtime-source" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None, "the exported page has no slot for an embedded runtime"
    return json.loads(match.group(1))


# --- the headline acceptance -------------------------------------------------


def test_lite_export_from_any_installation_points_at_a_runtime_that_exists(tmp_path):
    """The defect this work removes: an export from a git checkout was dead on arrival.

    The CDN URL was pinned to the exporting version whether or not that version
    had ever been published, so every export from a development install wrote a
    link that 404s. The local runtime cannot have that failure: it is the file
    that produced the scene.
    """
    output = tmp_path / "view.html"
    _view().export.html(str(output), shared_runtime=str(output.parent), skip_digestion=True)

    candidates = _runtime_candidates(output)
    assert candidates, "no runtime candidate was written"

    resolved = [(output.parent / candidate).resolve() for candidate in candidates]
    assert all(path.is_file() for path in resolved), (
        f"the exported page points at files that do not exist: {candidates}"
    )


def test_shared_runtime_directory_needs_no_network(tmp_path):
    output = tmp_path / "view.html"
    _view().export.html(str(output), shared_runtime=str(output.parent), skip_digestion=True)

    for candidate in _runtime_candidates(output):
        assert not candidate.startswith(("http://", "https://")), (
            f"a shared-directory export reaches the network: {candidate}"
        )


def test_lite_export_addresses_the_asset_relatively(tmp_path):
    """A relative URL is what survives being moved, served, and read from a subpage."""
    views = tmp_path / "_static" / "views"
    assets = tmp_path / "_static"
    views.mkdir(parents=True)

    output = views / "view.html"
    _view().export.html(
        str(output),
        shared_runtime=str(assets),
        skip_digestion=True,
    )

    candidates = _runtime_candidates(output)
    assert candidates == ["../viewer.js"], candidates
    assert (assets / RUNTIME_ASSET_NAME).is_file()


# --- version coherence of a shared asset -------------------------------------


def test_placing_the_asset_replaces_an_older_runtime(tmp_path):
    """Guard. Mutate `place_runtime_asset` to skip when the file merely exists
    and this must fail: several views sharing one stale runtime is the one
    incoherence the local path can produce."""
    stale = tmp_path / RUNTIME_ASSET_NAME
    stale.write_bytes(RUNTIME_ASSET_MARKER + b"\n// an older MolSysViewer build\n")

    placed = place_runtime_asset(tmp_path)

    assert placed.read_bytes() == runtime_asset_source().read_bytes()


def test_placing_the_asset_refuses_to_clobber_a_foreign_file(tmp_path):
    """Guard. `viewer.js` is a very common name.

    A user pointing shared_runtime at a directory that already holds their own
    bundle would lose it, with no warning and no copy. Only a file carrying our
    generated-bundle marker may be replaced.
    """
    theirs = tmp_path / RUNTIME_ASSET_NAME
    theirs.write_bytes(b"// somebody else's viewer, hand written\n")

    with pytest.raises(FileExistsError, match="not written by MolSysViewer"):
        place_runtime_asset(tmp_path)

    assert theirs.read_bytes() == b"// somebody else's viewer, hand written\n"


def test_placing_the_asset_twice_is_idempotent(tmp_path):
    first = place_runtime_asset(tmp_path)
    stamp = first.stat().st_mtime_ns
    second = place_runtime_asset(tmp_path)

    assert second == first
    assert second.stat().st_mtime_ns == stamp, "an unchanged asset was rewritten"


def test_placing_the_asset_refuses_a_missing_directory(tmp_path):
    """Guard. Writing a view that points at a directory nobody created would fail
    only when a reader opens the page."""
    with pytest.raises(NotADirectoryError):
        place_runtime_asset(tmp_path / "does-not-exist")


# --- the CDN path, supported but honest --------------------------------------


def test_cdn_export_refuses_a_development_version(tmp_path, monkeypatch):
    """Guard. Remove the release check and this must fail: the export would write
    a URL it can already tell is dead, and the failure would surface months later
    on somebody else's website."""
    monkeypatch.setattr("molsysviewer._version.__version__", "0.20.0+96.g6362914c.dirty")

    output = tmp_path / "view.html"
    with pytest.raises(ValueError, match="released version"):
        _view().export.html(str(output), shared_runtime="cdn", skip_digestion=True)


def test_cdn_export_from_a_release_writes_the_pinned_url(tmp_path, monkeypatch):
    monkeypatch.setattr("molsysviewer._version.__version__", "0.7.0")

    output = tmp_path / "view.html"
    _view().export.html(str(output), shared_runtime="cdn", skip_digestion=True)

    assert _runtime_candidates(output) == [
        "https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@0.7.0/dist/viewer.js"
    ]


@pytest.mark.parametrize(
    "version, released",
    [
        ("0.20.0", True),
        ("1.0.0", True),
        ("0.20.0+96.g6362914c.dirty", False),
        ("0.20.1.dev3", False),
    ],
)
def test_release_version_detection(version, released):
    assert is_release_version(version) is released


# --- no registry tail while the registry is behind ----------------------------


@pytest.mark.parametrize("version", ["0.20.0", "0.20.0+96.g6362914c.dirty", "0.20.1.dev3"])
def test_a_shared_export_addresses_the_local_runtime_and_nothing_else(
    tmp_path, monkeypatch, version
):
    """No CDN tail, at any version, unless the author asks for one.

    A pinned jsDelivr URL was appended here for a day, to rescue a shared view
    opened straight from a disk. It was removed because it 404s: npm stops at
    0.7.0 while this package is at 0.20.0, so the tail would write a dead URL
    into somebody else's published pages — the exact defect this design exists to
    remove. Reinstate it only when publishing to npm is a real release gate.
    """
    monkeypatch.setattr("molsysviewer._version.__version__", version)
    output = tmp_path / "view.html"
    _view().export.html(str(output), shared_runtime=str(tmp_path), skip_digestion=True)

    assert _runtime_candidates(output) == [f"./{RUNTIME_ASSET_NAME}"]
    assert "jsdelivr" not in output.read_text(encoding="utf-8")


# --- explicit candidates and refusals ----------------------------------------


def test_explicit_candidates_are_preserved_in_order(tmp_path):
    output = tmp_path / "view.html"
    explicit = ["./viewer.js", "https://example.org/viewer.js"]
    _view().export.html(
        str(output), shared_runtime=explicit, skip_digestion=True
    )

    assert _runtime_candidates(output) == explicit


def test_without_shared_runtime_the_file_stands_alone(tmp_path):
    """The default carries everything, so it addresses nothing.

    Not one URL, not one candidate, not one sibling file: what makes this export
    openable from a disk with no network is that there is nothing left to fetch.
    """
    output = tmp_path / "view.html"
    _view().export.html(str(output), skip_digestion=True)
    html = output.read_text(encoding="utf-8")

    assert _runtime_candidates(output) == []
    assert _embedded_runtime(output).startswith("// @generated"), (
        "the self-contained export does not carry the runtime it needs"
    )
    assert not (tmp_path / RUNTIME_ASSET_NAME).exists(), (
        "a self-contained export placed a shared asset it does not use"
    )
    for host in ("cdn.jsdelivr.net", "cdnjs.cloudflare.com", "unpkg.com"):
        assert host not in html, f"a self-contained export still reaches {host}"


# --- computing the embed path ------------------------------------------------


def test_embed_iframe_computes_the_path_from_the_page(tmp_path):
    """The one step of embedding that fails silently: counting `../` by hand.

    The export succeeds, the build succeeds, and the reader gets an empty frame.
    """
    markup = msv.tools.embed_iframe(
        str(tmp_path / "_static" / "views" / "1tcd.html"),
        path=str(tmp_path / "content" / "user" / "page.md"),
    )

    assert 'src="../../_static/views/1tcd.html"' in markup
    assert "<iframe" in markup and "</iframe>" in markup


def test_embed_iframe_accepts_its_own_defaults(tmp_path):
    """Documented call, digestion included.

    Every other test here once passed `skip_digestion=True`, so the argument
    layer was never exercised and `width="100%"` — the function's own default —
    was rejected by the length digester that serves shapes and boxes. The
    documented call raised while the tests were green.
    """
    markup = msv.tools.embed_iframe(
        str(tmp_path / "v.html"), path=str(tmp_path / "p.ipynb")
    )

    assert 'width="100%"' in markup and 'height="480px"' in markup


def test_embed_iframe_takes_pixels_as_a_number(tmp_path):
    markup = msv.tools.embed_iframe(
        str(tmp_path / "v.html"), path=str(tmp_path / "p.ipynb"), width=600, height=320,
    )

    assert 'width="600px"' in markup and 'height="320px"' in markup


def test_embed_iframe_marks_a_sibling_path_as_relative(tmp_path):
    """A bare name would be read as a URL fragment by some renderers."""
    markup = msv.tools.embed_iframe(
        str(tmp_path / "1tcd.html"),
        path=str(tmp_path / "page.md"),
    )

    assert 'src="./1tcd.html"' in markup


def test_embed_iframe_renders_in_a_notebook_and_is_still_a_string(tmp_path):
    """One call for both ways of embedding.

    Plain text would force `print()` on the notebook path; a display object alone
    would make pasting into a Markdown page awkward. Both must keep working.
    """
    markup = msv.tools.embed_iframe(
        str(tmp_path / "v.html"), path=str(tmp_path / "p.ipynb")
    )

    assert isinstance(markup, str), "the result stopped behaving as a string"
    assert markup._repr_html_() == str(markup), "the result no longer renders"
    assert markup.startswith("<iframe")


def test_embed_iframe_honours_the_requested_size(tmp_path):
    markup = msv.tools.embed_iframe(
        str(tmp_path / "v.html"), path=str(tmp_path / "p.md"),
        height="640px", width="80%",
    )

    assert 'height="640px"' in markup and 'width="80%"' in markup


def test_tools_export_runtime_asset_places_the_bundled_runtime(tmp_path):
    placed = msv.tools.export_runtime_asset(str(tmp_path), skip_digestion=True)

    assert placed == (tmp_path / RUNTIME_ASSET_NAME).resolve()
    assert placed.read_bytes() == runtime_asset_source().read_bytes()


# --- what the page sits on ----------------------------------------------------


def _page(tmp_path, **kwargs) -> str:
    output = tmp_path / "view.html"
    _view().export.html(str(output), skip_digestion=True, **kwargs)
    return output.read_text(encoding="utf-8")


def _page_css(html: str) -> str:
    """The page's own stylesheet.

    Not the whole file: a self-contained export carries the runtime inside it,
    and the runtime mentions `prefers-color-scheme` itself. Asserting over the
    whole document would pass, or fail, for the wrong reason.
    """
    match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    assert match is not None, "the exported page has no stylesheet"
    return match.group(1)


def test_the_default_page_asks_the_page_around_it_first(tmp_path):
    """An exported view is read on a screen its author never sees.

    So the page asks where it lands: the host document when there is one — which
    is same-origin, because a view and the site embedding it are served together
    — and the reader's preference when there is not. Asking the host is what
    makes a documentation theme's own light/dark switch work, since that is a
    decision of the site and no media query reports it.

    The stylesheet carries the fallback too, because the runtime is megabytes:
    without it a dark page shows white for the seconds it takes to boot.
    """
    html = _page(tmp_path)

    assert "prefers-color-scheme: dark" in _page_css(html)
    assert '"background_mode":"auto"' in html
    for reading_the_host in ("window.parent.document", "MutationObserver"):
        assert reading_the_host in html, (
            f"the page stopped following the site it is embedded in ({reading_the_host})"
        )
    assert "window.self !== window.top" not in html, (
        "the default page gave away its background to whatever embeds it"
    )


def test_a_transparent_page_defers_to_the_host_only_when_embedded(tmp_path):
    """Alone it must still have a background; embedded it must have none.

    No CSS selector distinguishes the two, so the page decides it in a script
    that runs before anything is painted — otherwise the transparent case shows
    a colour and then takes it away.
    """
    html = _page(tmp_path, background="transparent")

    assert '"background_mode":"transparent"' in html
    assert "window.self !== window.top" in html
    assert "prefers-color-scheme: dark" in _page_css(html), (
        "a transparent page opened on its own would have no background at all"
    )


@pytest.mark.parametrize("fixed", ["white", "dark"])
def test_a_fixed_page_ignores_the_reader(tmp_path, fixed):
    html = _page(tmp_path, background=fixed)

    assert f'"background_mode":"{fixed}"' in html
    assert "prefers-color-scheme" not in _page_css(html), (
        f"background={fixed!r} still consulted the reader's preference"
    )


def test_the_html_export_refuses_a_background_it_cannot_honour(tmp_path):
    """`"current"` is an image-export answer: there is no current anything here."""
    from molsysviewer._private.exceptions import ArgumentError

    with pytest.raises(ArgumentError):
        _view().export.html(str(tmp_path / "v.html"), background="current")
    with pytest.raises(ArgumentError):
        _view().export.html(str(tmp_path / "v.html"), background="#ffffff")
