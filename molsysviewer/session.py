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
from ._private.exceptions.interaction_analysis_error import InteractionAnalysisError
from .interactions import _analysis_signature

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
        raise SessionFormatError("This file is not a MolSysViewer session: it has no manifest.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SessionFormatError("The session manifest is not readable JSON.") from error

    if manifest.get("format") != SESSION_FORMAT:
        raise SessionFormatError(f"This file declares format {manifest.get('format')!r}, not {SESSION_FORMAT!r}.")
    version = manifest.get("version")
    if version != SESSION_VERSION:
        raise SessionFormatError(
            f"Unsupported session version: {version!r}. This build reads version {SESSION_VERSION}."
        )
    return manifest


def _validate_session_scene(molsys: Any, state: dict) -> None:
    """Restore an isolated scene before an existing destination is changed.

    Borrow the incoming system rather than copying its trajectory. The scene
    importer reads scientific data and builds independent viewer-owned objects.
    Closing the temporary view also releases its widget registry entries.
    """
    from .viewer import MolSysView

    with MolSysView() as candidate:
        candidate.apply_system_edit(
            molsys, load_blocks="collapse", interactions_policy="preserve"
        )
        if state.get("sources") is not None and candidate._prepare_source_import(state["sources"]) is None:
            raise SessionFormatError("Session source maps refer to a different ordered molecular system.")
        candidate.import_state(state)


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
        analyses = getattr(molsys, "interactions", {})
        signatures = {name: _analysis_signature(result) for name, result in analyses.items()}
        writer = getattr(getattr(msm, "h5msm", None), "write", None)
        if analyses and writer is None:
            raise InteractionAnalysisError(reason="backend_required")
        if writer is not None:
            # The public 0.5 writer retains submitted array precision and named
            # analyses. Its default conversion route rejects float_precision.
            writer(molsys, str(structure_path))
        else:
            # The legacy 0.4 writer defaults to float32: request double so an
            # arbitrary public coordinate edit survives the binding round trip.
            msm.convert(molsys, to_form=str(structure_path), float_precision="double")
        manifest = {
            "format": SESSION_FORMAT,
            "version": SESSION_VERSION,
            "molsysviewer": __version__,
            **({"interaction_analyses": {"version": 1, "signatures": signatures}} if signatures else {}),
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
            with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
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

    Returns the viewer showing it. An existing ``view`` has its system and scene
    replaced after validating the scientific manifest. Factory options in ``kwargs``
    configure a newly created viewer; the complete session system is always loaded.
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
            structure_path = str(Path(workspace) / member)
            if manifest.get("interaction_analyses") is not None:
                reader = getattr(getattr(msm, "h5msm", None), "read", None)
                if reader is None:
                    raise InteractionAnalysisError(reason="backend_required")
                molsys = reader(structure_path)
            else:
                molsys = msm.convert(structure_path, to_form="molsysmt.MolSys")

    recorded = manifest.get("interaction_analyses")
    if recorded is not None:
        if (
            not isinstance(recorded, dict)
            or recorded.get("version") != 1
            or not isinstance(recorded.get("signatures"), dict)
        ):
            raise SessionFormatError("Unsupported interaction-analysis manifest in this session.")
        analyses = getattr(molsys, "interactions", {})
        if set(analyses) != set(recorded["signatures"]):
            raise InteractionAnalysisError(reason="session_mismatch", extra={"name": "collection"})
        for name, signature in recorded["signatures"].items():
            if not isinstance(signature, str) or _analysis_signature(analyses[name]) != signature:
                raise InteractionAnalysisError(reason="session_mismatch", extra={"name": name})

    if view is not None:
        _validate_session_scene(molsys, state)

    restored = new_view(view=view, **kwargs)
    try:
        restored.load(molsys, mode="replace")
        if state.get("sources") is not None and restored._prepare_source_import(state["sources"]) is None:
            raise SessionFormatError("Session source maps refer to a different ordered molecular system.")
        restored.import_state(state)
    except Exception:
        if view is None:
            restored.close()
        raise
    return restored
