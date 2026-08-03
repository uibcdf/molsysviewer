"""Placement and addressing of the bundled runtime for exported views.

A ``mode="lite"`` export does not carry the runtime: it points at one. Where it
points decides whether the exported page still works later, offline, and on
somebody else's website.

The default answer is the runtime that ships inside the installed package. It is
version-exact with the scene it renders by construction, it needs no registry, no
CDN and no network, and an author who upgrades MolSysViewer and rebuilds their
site gets the new runtime deterministically. See
`devguide/pending_proposals/embedding_views_in_external_documentation.md`.
"""

from __future__ import annotations

import os
from pathlib import Path

RUNTIME_ASSET_NAME = "viewer.js"

# esbuild writes this banner at the top of every bundle it produces for us
# (`js/scripts/build-runtime.mjs`). It is how a file we may overwrite is told
# apart from a file that merely shares a very common name.
RUNTIME_ASSET_MARKER = b"// This file is generated from js/src/index.ts"


def runtime_asset_source() -> Path:
    """Absolute path of the runtime that ships with this installation."""
    return (Path(__file__).resolve().parent.parent / RUNTIME_ASSET_NAME).resolve()


def is_release_version(version: str) -> bool:
    """True when ``version`` is a plain release, not a development build.

    Only a release can exist in a package registry. ``versioningit`` renders a
    working tree as ``0.20.0+96.g6362914c.dirty`` and a pre-release as
    ``0.20.1.dev3``; neither is ever published, so a CDN URL built from one is
    dead before it is written.
    """
    return "+" not in version and ".dev" not in version


def place_runtime_asset(directory: str | os.PathLike[str]) -> Path:
    """Ensure the packaged runtime is present in ``directory`` and return it.

    Idempotent **by content**, not by existence. A shared asset serving several
    exported views is the one thing in this design that can drift: regenerate one
    view after upgrading MolSysViewer and its scene would meet the previous
    runtime. Comparing bytes and overwriting on difference is what keeps the
    shared asset coherent, and it needs no sidecar metadata that could itself go
    stale.
    """
    source = runtime_asset_source()
    if not source.is_file():
        raise FileNotFoundError(
            f"The MolSysViewer runtime is missing from the installed package: {source}. "
            "A source checkout needs `npm run build:runtime` in molsysviewer/js/."
        )

    target_dir = Path(directory)
    if not target_dir.is_dir():
        raise NotADirectoryError(
            f"runtime assets directory does not exist: {target_dir}. "
            "Create it before exporting, so a view is never written pointing at nothing."
        )

    target = target_dir / RUNTIME_ASSET_NAME
    payload = source.read_bytes()
    if target.is_file():
        existing = target.read_bytes()
        if existing == payload:
            return target.resolve()
        if RUNTIME_ASSET_MARKER not in existing[:512]:
            # `viewer.js` is a very common name. Overwriting a file that is not
            # ours would destroy somebody's own bundle with no warning and no
            # copy, so refuse and say where. An older or newer MolSysViewer
            # runtime carries the marker and is replaced normally.
            raise FileExistsError(
                f"{target} exists and was not written by MolSysViewer, so it will not be "
                "overwritten. Choose another directory for the shared runtime, or remove "
                "that file if it is no longer needed."
            )
    target.write_bytes(payload)
    return target.resolve()


def relative_runtime_url(html_path: str | os.PathLike[str], asset_path: str | os.PathLike[str]) -> str:
    """URL for ``asset_path`` as seen from the page written at ``html_path``.

    The exported page resolves each candidate with ``new URL(candidate,
    window.location.href)``, so a relative path is resolved against the page. It
    is computed here rather than by the caller because a wrong one fails only
    when a reader opens the page, long after the export succeeded.
    """
    html_dir = Path(html_path).resolve().parent
    relative = os.path.relpath(Path(asset_path).resolve(), start=html_dir)
    posix = Path(relative).as_posix()
    return posix if posix.startswith((".", "/")) else f"./{posix}"
