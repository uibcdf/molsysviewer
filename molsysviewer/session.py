"""A session: the scene *and* the system it was built on, in one portable file.

`save_state` writes what a user built on top of a structure; reopening it requires that
they load the right structure first, and know which one it was. That gap is what
`session_reproducibility.md` has carried as an open question since Phase 6, against a
promise the same document states plainly: save, close, reload elsewhere, continue as if
you had never left. A state document cannot keep that promise on its own.

A session file closes it. It is a zip holding three members:

    manifest.json      what this file is, and what is inside it
    state.json         the `export_state` document, unchanged
    structure.h5msm    the molecular system, in MolSysMT's own format

The structure format is the part worth explaining. MolSysMT writes `.pdb` and `.h5msm`
from a `MolSys` and not `.bcif`, so the usual preference for binary CIF over PDB does not
apply here -- it is about reading what a user supplies. Between the two that can be
written, `.pdb` collapses chains and misassigns waters, and carries one structure where a
trajectory has thousands. `.h5msm` is MolSysMT's own form: measured, it round-trips 62
atoms across 5,000 structures, and -- the property this design depends on -- the
structure's topological fingerprint survives it unchanged. Without that a reloaded
session would warn that its own structure was not the one its own state was written for.
"""

from __future__ import annotations

import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from depdigest import dep_digest
from smonitor import signal

from ._private.argdigest import digest

SESSION_FORMAT = "molsysviewer-session"
SESSION_VERSION = 1

_MANIFEST_MEMBER = "manifest.json"
_STATE_MEMBER = "state.json"
_STRUCTURE_MEMBER = "structure.h5msm"


class SessionFormatError(ValueError):
    """A file that is not a MolSysViewer session, or is one this build cannot read."""


def _read_manifest(archive: zipfile.ZipFile) -> dict:
    try:
        manifest = json.loads(archive.read(_MANIFEST_MEMBER).decode("utf-8"))
    except KeyError as error:
        raise SessionFormatError(
            "This file is not a MolSysViewer session: it has no manifest."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SessionFormatError("The session manifest is not readable JSON.") from error

    if manifest.get("format") != SESSION_FORMAT:
        raise SessionFormatError(
            f"This file declares format {manifest.get('format')!r}, not {SESSION_FORMAT!r}."
        )
    version = manifest.get("version")
    if version != SESSION_VERSION:
        raise SessionFormatError(
            f"Unsupported session version: {version!r}. This build reads version "
            f"{SESSION_VERSION}."
        )
    return manifest


def save_session(view: Any, path: str | os.PathLike[str]) -> None:
    """Write the scene and the system it was built on to one portable file.

    Refuses when no system is loaded: a session without a structure is a state document,
    and `save_state` already writes those. Saying so is better than writing a file that
    calls itself a session and cannot reopen as one.
    """
    import molsysmt as msm

    from ._version import __version__

    molsys = getattr(view, "_molsys", None)
    if molsys is None:
        raise ValueError(
            "No molecular system is loaded, so there is no session to save. Use "
            "save_state(path) to write the scene on its own."
        )

    state = view.export_state()
    destination = Path(path)
    temporary_path: Path | None = None
    with tempfile.TemporaryDirectory() as workspace:
        structure_path = Path(workspace) / _STRUCTURE_MEMBER
        msm.convert(molsys, to_form=str(structure_path))
        manifest = {
            "format": SESSION_FORMAT,
            "version": SESSION_VERSION,
            "molsysviewer": __version__,
            "structure": {
                "member": _STRUCTURE_MEMBER,
                "form": "molsysmt.h5msm",
                # Repeated from the state document on purpose: a reader can tell what is
                # in the file without parsing the scene, and a mismatch between the two
                # is evidence the archive was assembled by hand.
                **{key: value for key, value in (state.get("structure") or {}).items()},
            },
        }
        try:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
            with zipfile.ZipFile(
                temporary_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                archive.writestr(_MANIFEST_MEMBER, json.dumps(manifest, indent=2, sort_keys=True))
                archive.writestr(_STATE_MEMBER, json.dumps(state, indent=2, sort_keys=True))
                archive.write(structure_path, _STRUCTURE_MEMBER)
            os.replace(temporary_path, destination)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise


@dep_digest("molsysmt")
@signal(tags=["state", "factory"])
@digest()
def load_session(
    path: str | os.PathLike[str],
    *,
    view: Any = None,
    skip_digestion: bool = False,
    **kwargs: Any,
) -> Any:
    """Reopen a session: its system, then the scene that was built on it.

    Returns the viewer showing it. Unlike `load_state`, nothing has to be loaded first --
    that is the whole point of the format.
    """
    import molsysmt as msm

    from .new_view import new_view

    source = Path(path)
    with zipfile.ZipFile(source) as archive:
        manifest = _read_manifest(archive)
        try:
            state = json.loads(archive.read(_STATE_MEMBER).decode("utf-8"))
        except KeyError as error:
            raise SessionFormatError("The session carries no state document.") from error
        member = str((manifest.get("structure") or {}).get("member") or _STRUCTURE_MEMBER)
        with tempfile.TemporaryDirectory() as workspace:
            try:
                archive.extract(member, workspace)
            except KeyError as error:
                raise SessionFormatError(
                    f"The session names {member!r} as its structure, and does not contain it."
                ) from error
            molsys = msm.convert(str(Path(workspace) / member), to_form="molsysmt.MolSys")

    restored = new_view(molsys, view=view, **kwargs)
    restored.import_state(state)
    return restored
