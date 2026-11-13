"""An offline Movie presentation using the existing scene and timeline owners."""

import asyncio
import hashlib
import inspect
import math
import os
import tempfile
import time
from copy import deepcopy
from numbers import Real
from pathlib import Path

from ._movie_baseline import check_idle
from ._movie_composition import overlay_requirements, overlay_revisions, overlays_unchanged
from ._movie_endpoint import check_movie_revision
from ._movie_export import _dimensions, _visible_overlays
from ._movie_playback import _revisions
from .frontend_requests import FrontendRequestError
from .visual_capture import _capture_owned_call


def _presentation(movie, width, height, include_overlays):
    from . import MolSysView

    view = movie._view
    check_movie_revision(movie)
    check_idle(movie)
    timeline = movie._require_timeline()
    scene = view.export_state(skip_digestion=True)
    timeline.check_binding(view._source_state_binding(), scene)
    timeline.check_scene(scene)
    recipe = timeline.to_dict()
    baseline = recipe["baseline"]["scene"]
    excluded = sorted(set(_visible_overlays(view, baseline) + _visible_overlays(view, scene)))
    required, context = overlay_requirements(view, scene)
    # Browser playback cannot delegate a coordinate-dependent selection to Python.
    if any(row.get("mode") == "dynamic" for row in baseline.get("regions", [])):
        raise ValueError("Movie HTML currently requires static regions; materialize dynamic regions explicitly.")

    # Borrow the scientific object exactly as state-import preflight does. Only
    # this isolated scene owner is restored; no molecular preparation is run.
    with MolSysView() as candidate:
        candidate.apply_system_edit(view.molsys, load_blocks="collapse", interactions_policy="preserve")
        candidate._restore_state_contents(deepcopy(baseline), clear_first=True, on_conflict="raise")
        candidate.player.pause(skip_digestion=True)
        candidate._last_camera_snapshot = deepcopy(recipe["baseline"]["camera"])
        for name in ("legend", "trajectory_plot"):
            if include_overlays and name in view._scene_look:
                candidate._scene_look[name] = deepcopy(view._scene_look[name])
            else:
                candidate._scene_look.pop(name, None)
        messages = candidate._build_static_export_snapshot()
        for message in messages:
            if message.get("op") == "set_interaction_series" and any(
                frame["status"] not in {"evaluated", "unevaluated", "excluded"} for frame in message["frames"]
            ):
                raise ValueError(
                    "Movie HTML requires complete supported interaction projections; narrow unsupported or over-limit visual filters."
                )
        # Playback controls and all data are in this one file. No runtime CDN,
        # original path, server, optional codec or Python kernel is required.
        runtime = candidate.widget._viewer_js_source
        from .._version import __version__

        manifest = {
            "schema": "molsysviewer.movie_web@1",
            "status": "completed",
            "recipe": recipe,
            "assets": {
                "policy": "embedded-offline",
                "runtime_sha256": hashlib.sha256(runtime.encode()).hexdigest(),
                "molsysviewer": __version__,
            },
            "viewport": {"width": width, "height": height, "responsive": True},
            "composition": {
                "native_annotations": True,
                "dom_overlays": "live-dom-overlays@1" if include_overlays else "explicitly-excluded",
                "included_dom_overlays": required if include_overlays else [],
                "excluded_dom_overlays": [] if include_overlays else excluded,
                "source_context": context,
            },
            "controls": ["play", "pause", "seek", "restart"],
        }
        html = candidate._build_lite_html(
            title="MolSysViewer Movie",
            include_controls=True,
            include_popout=False,
            messages=messages,
            inline_messages=True,
            runtime_source=runtime,
            movie_presentation=manifest,
        )
    return timeline, _revisions(view), overlay_revisions(view), html, manifest


async def export_movie_web(movie, path, *, width, height, overwrite, include_overlays, timeout, on_progress):
    _dimensions(width, height)
    if type(overwrite) is not bool or type(include_overlays) is not bool:
        raise ValueError("Movie overwrite/include_overlays must be booleans.")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, Real)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 300
    ):
        raise ValueError("Movie HTML timeout must be in (0, 300] seconds.")
    if on_progress is not None and not callable(on_progress):
        raise ValueError("Movie on_progress must be a synchronous callable.")
    path = Path(path).expanduser().absolute()
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    if not path.parent.is_dir():
        raise FileNotFoundError(path.parent)
    deadline = time.monotonic() + timeout
    job = object()

    def prepare():
        result = _presentation(movie, width, height, include_overlays)
        movie._export_job = job
        movie._studio_runtime_changed()
        return result

    def verify():
        check_movie_revision(movie)
        if (
            movie._view.closed
            or movie._export_job is not job
            or movie._timeline is not timeline
            or _revisions(movie._view) != revisions
            or not overlays_unchanged(movie._view, overlays)
        ):
            raise FrontendRequestError(reason="movie_export_superseded")

    def publish():
        verify()
        if on_progress is not None:
            value = on_progress({"phase": "publish", "format": "html"})
            if inspect.isawaitable(value):
                if inspect.iscoroutine(value):
                    value.close()
                raise ValueError("Movie on_progress must be synchronous.")
            verify()
        with tempfile.TemporaryDirectory(dir=path.parent, prefix=f".{path.name}.movie-") as directory:
            staged = Path(directory) / "presentation.html"
            staged.write_text(html, encoding="utf-8")
            if overwrite:
                os.replace(staged, path)
            else:
                os.link(staged, path)
        return {"path": str(path), "manifest": deepcopy(manifest), "bytes": path.stat().st_size}

    try:
        timeline, revisions, overlays, html, manifest = await _capture_owned_call(
            movie._view, prepare, deadline=deadline
        )
        # Yield before publication so cancellation cannot leave an apparently
        # successful output when its initiating Studio panel has already closed.
        await asyncio.sleep(0)
        return await _capture_owned_call(movie._view, publish, deadline=deadline)
    finally:
        if movie._export_job is job:
            movie._export_job = None
            movie._studio_runtime_changed()
