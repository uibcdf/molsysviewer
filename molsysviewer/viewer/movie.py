from __future__ import annotations

import base64
import io
import json
import math
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from smonitor import signal

from .._private.argdigest import digest
from ._movie_timeline import MOVIE_TIMELINE_VERSION, _MovieTimeline

_EASING_VALUES = frozenset({"linear", "ease-in", "ease-out", "ease-in-out"})
_MOLSYSMOVIE_VERSION = 1


class MovieManager:
    """Manages a timeline of keyframes for browser playback and video export.

    Access via ``view.movie``.

    Timeline construction
    ---------------------
    add_keyframe(time_ms, ...)           Add a single keyframe.
    add_camera_orbit(duration_ms, ...)   Generate orbit keyframes.
    add_structure_sweep(...)             Generate structure-sweep keyframes.
    add_visibility_transition(...)       Step visibility at a given time.
    clear()                              Reset the timeline.

    Playback / export
    -----------------
    play(loop=False)                     Preview animation in browser.
    stop()                               Stop browser playback.
    export(path, fps, ...)               Export to MP4 / GIF / WebM.
    await export_async(path, ...)       Stream a version-2 Movie to media.

    Serialization
    -------------
    to_dict()                            Serialise timeline to a plain dict.
    from_dict(data)                      Replace timeline from a plain dict.
    save(path)                           Write timeline to JSON file.
    load(path)                           Load timeline from JSON file.
    """

    def __init__(self, view: Any) -> None:
        self._view = view
        self._keyframes: list[dict] = []
        self._timeline: _MovieTimeline | None = None
        self._seek_request = None
        self._playback = None
        self._export_job = None
        self._rebase_capture = None
        self._import_review = None
        self._studio_revision = 0
        self._studio = None

    # ── Timeline construction ─────────────────────────────────────────────

    @signal()
    @digest()
    def add_keyframe(
        self,
        time_ms: float,
        *,
        camera: dict | None = None,
        structure_index: int | None = None,
        layer_visibility: dict[str, bool] | None = None,
        easing: str = "linear",
        skip_digestion: bool = False,
    ) -> None:
        """Add a keyframe to the timeline.

        Parameters
        ----------
        time_ms
            Timestamp in milliseconds. Must be strictly greater than the
            last existing keyframe.
        camera
            Camera snapshot dict with ``position`` and ``target`` in Å and
            dimensionless ``up``. Use ``view.camera.get_snapshot()`` to capture the
            current camera. ``None`` means no camera change at this point.
        structure_index
            Structure (trajectory frame) index to show at this time.
            ``None`` means no change.
        layer_visibility
            ``{tag: visible}`` mapping for layers/regions. Missing tags are
            unchanged. Applied as a step change at this keyframe's time.
        easing
            Easing function for the segment [this_keyframe, next_keyframe].
            One of ``"linear"``, ``"ease-in"``, ``"ease-out"``,
            ``"ease-in-out"``.
        """
        self._legacy_only()
        if easing not in _EASING_VALUES:
            raise ValueError(f"easing must be one of {sorted(_EASING_VALUES)!r}, got {easing!r}")
        time_ms = float(time_ms)
        if self._keyframes and time_ms <= self._keyframes[-1]["time_ms"]:
            raise ValueError(
                f"time_ms={time_ms} must be strictly greater than the last "
                f"keyframe at time_ms={self._keyframes[-1]['time_ms']}"
            )
        kf: dict = {"time_ms": time_ms, "easing": easing}
        if camera is not None:
            _validate_camera_snapshot(camera)
            kf["camera"] = {k: list(v) for k, v in camera.items() if k in ("position", "target", "up")}
        if structure_index is not None:
            kf["structure_index"] = int(structure_index)
        if layer_visibility is not None:
            kf["layer_visibility"] = {str(k): bool(v) for k, v in layer_visibility.items()}
        self._keyframes.append(kf)
        self._invalidate_observation()

    @signal()
    @digest()
    def add_visibility_transition(
        self,
        tag: str,
        visible: bool,
        at_time_ms: float,
        *,
        skip_digestion: bool = False,
    ) -> None:
        """Insert or update a visibility step for a layer/region tag.

        If a keyframe already exists at ``at_time_ms``, the entry is merged
        into it. Otherwise a new keyframe with no camera or structure change
        is inserted at the correct sorted position.

        Parameters
        ----------
        tag
            Layer or region tag.
        visible
            Target visibility at this time.
        at_time_ms
            Timestamp in milliseconds.
        """
        self._legacy_only()
        at_time_ms = float(at_time_ms)
        for kf in self._keyframes:
            if kf["time_ms"] == at_time_ms:
                kf.setdefault("layer_visibility", {})[str(tag)] = bool(visible)
                return
        new_kf: dict = {
            "time_ms": at_time_ms,
            "easing": "linear",
            "layer_visibility": {str(tag): bool(visible)},
        }
        insert_at = next(
            (i for i, kf in enumerate(self._keyframes) if kf["time_ms"] > at_time_ms),
            len(self._keyframes),
        )
        self._keyframes.insert(insert_at, new_kf)

    @signal()
    @digest()
    def add_camera_orbit(
        self,
        duration_ms: float = 5000.0,
        *,
        n_turns: float = 1.0,
        start_time_ms: float | None = None,
        center: list[float] | None = None,
        n_keyframes: int = 36,
        easing: str = "linear",
        skip_digestion: bool = False,
    ) -> None:
        """Append keyframes that rotate the camera around a center point.

        The camera maintains constant distance and elevation. Uses the
        current camera state as the starting position and orientation.

        Parameters
        ----------
        duration_ms
            Total duration of the orbit in milliseconds.
        n_turns
            Number of full 360° rotations.
        start_time_ms
            Timeline offset for the first keyframe. Defaults to
            ``view.movie.duration_ms`` (appends after the last keyframe).
        center
            Orbit center in Å ``[x, y, z]``. Defaults to the current
            camera target.
        n_keyframes
            Number of keyframes generated per full turn.
        easing
            Easing applied to each inter-keyframe segment.
        """
        self._legacy_only()
        if easing not in _EASING_VALUES:
            raise ValueError(f"easing must be one of {sorted(_EASING_VALUES)!r}, got {easing!r}")
        snap = self._view.camera.get_snapshot(skip_digestion=True)
        if snap is None:
            raise RuntimeError("No camera snapshot available. Load a system first.")
        pos = list(snap["position"])
        target = list(snap["target"])
        up = list(snap["up"])

        if center is None:
            center = list(target)
        else:
            center = [float(c) for c in center]

        radial = [pos[i] - center[i] for i in range(3)]
        radius = math.sqrt(sum(r * r for r in radial))
        if radius < 1e-9:
            raise ValueError("Camera is at the orbit center; cannot determine orbit radius.")
        radial_unit = [r / radius for r in radial]

        right = _cross(radial_unit, up)
        right_len = math.sqrt(sum(r * r for r in right))
        if right_len < 1e-9:
            raise ValueError("Camera up vector is parallel to the radial; cannot compute orbit plane.")
        right_unit = [r / right_len for r in right]

        if start_time_ms is None:
            start_time_ms = self.duration_ms if self._keyframes else 0.0
        start_time_ms = float(start_time_ms)
        duration_ms = float(duration_ms)

        total_kf = int(n_keyframes * abs(n_turns)) + 1
        for i in range(total_kf):
            t = i / (total_kf - 1) if total_kf > 1 else 0.0
            theta = 2.0 * math.pi * n_turns * t
            new_radial = [math.cos(theta) * radial_unit[j] + math.sin(theta) * right_unit[j] for j in range(3)]
            new_pos = [center[j] + radius * new_radial[j] for j in range(3)]
            kf_time = start_time_ms + duration_ms * t
            camera_kf = {"position": new_pos, "target": list(center), "up": list(up)}

            if self._keyframes and kf_time <= self._keyframes[-1]["time_ms"]:
                last_t = self._keyframes[-1]["time_ms"]
                if abs(kf_time - last_t) < 1e-3:
                    self._keyframes[-1]["camera"] = camera_kf
                    continue
                raise ValueError(
                    f"Orbit keyframe at time_ms={kf_time:.1f} collides with "
                    f"existing keyframe at time_ms={last_t:.1f}. "
                    "Adjust start_time_ms."
                )
            kf: dict = {"time_ms": kf_time, "easing": easing, "camera": camera_kf}
            self._keyframes.append(kf)
        self._invalidate_observation()

    @signal()
    @digest()
    def add_structure_sweep(
        self,
        *,
        from_index: int = 0,
        to_index: int | None = None,
        start_time_ms: float | None = None,
        duration_ms: float | None = None,
        end_time_ms: float | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Append keyframes that step through structure (trajectory) indices.

        Generates one keyframe per structure index between ``from_index``
        and ``to_index`` (inclusive). Only ``structure_index`` is set; the
        camera is not touched.

        Parameters
        ----------
        from_index
            First structure index.
        to_index
            Last structure index (inclusive). Defaults to
            ``view.player.n_structures - 1``.
        start_time_ms
            Timeline offset for the first keyframe. Defaults to
            ``view.movie.duration_ms`` (appends after the last keyframe).
        duration_ms
            Total sweep duration in milliseconds. Provide this or
            ``end_time_ms``.
        end_time_ms
            Absolute time of the last keyframe. Alternative to
            ``duration_ms``.
        """
        self._legacy_only()
        if to_index is None:
            n = self._view.player.n_structures
            if not n:
                raise RuntimeError("No molecular system loaded; cannot determine to_index. Pass to_index explicitly.")
            to_index = n - 1

        from_index = int(from_index)
        to_index = int(to_index)
        if from_index > to_index:
            raise ValueError(f"from_index ({from_index}) must be ≤ to_index ({to_index}).")

        if start_time_ms is None:
            start_time_ms = self.duration_ms if self._keyframes else 0.0
        start_time_ms = float(start_time_ms)

        if duration_ms is None and end_time_ms is None:
            raise ValueError("Provide either duration_ms or end_time_ms.")
        if duration_ms is not None and end_time_ms is not None:
            raise ValueError("Provide duration_ms or end_time_ms, not both.")
        if end_time_ms is not None:
            duration_ms = float(end_time_ms) - start_time_ms
        duration_ms = float(duration_ms)  # type: ignore[arg-type]
        if duration_ms <= 0:
            raise ValueError(f"duration_ms must be positive, got {duration_ms}.")

        n_steps = to_index - from_index
        for i in range(n_steps + 1):
            t = i / max(n_steps, 1)
            kf_time = start_time_ms + duration_ms * t
            structure_index = from_index + i
            if self._keyframes and kf_time <= self._keyframes[-1]["time_ms"]:
                last_t = self._keyframes[-1]["time_ms"]
                if abs(kf_time - last_t) < 1e-3:
                    self._keyframes[-1]["structure_index"] = structure_index
                    continue
                raise ValueError(
                    f"Sweep keyframe at time_ms={kf_time:.1f} collides with "
                    f"existing keyframe at time_ms={last_t:.1f}. "
                    "Adjust start_time_ms."
                )
            kf: dict = {
                "time_ms": kf_time,
                "easing": "linear",
                "structure_index": structure_index,
            }
            self._keyframes.append(kf)
        self._invalidate_observation()

    @signal()
    @digest()
    def clear(self, *, skip_digestion: bool = False) -> None:
        """Remove the current recipe without changing the visible scene."""
        self._keyframes = []
        self._timeline = None
        self._invalidate_observation()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def duration_ms(self) -> float:
        """Total duration in milliseconds (0.0 if empty)."""
        if self._timeline is not None:
            return self._timeline.duration_ms
        return self._keyframes[-1]["time_ms"] if self._keyframes else 0.0

    @property
    def keyframes(self) -> list[dict]:
        """Return detached keyframe data for inspection."""
        return deepcopy(self._keyframes)

    @signal()
    @digest()
    def set_baseline(
        self, duration_ms: float, *, camera: dict, state: dict | None = None, skip_digestion: bool = False
    ) -> None:
        """Start a track recipe with a detached scene and an explicit camera pose.

        The camera's position and target use angstroms. Its up vector is
        dimensionless. The duration is in milliseconds. Omit `state` to
        capture the current Python scene state, including declared environment
        settings. This starts an empty set of
        tracks, which is a valid static hold for the specified duration.
        """
        binding = self._view._source_state_binding()
        if binding is None:
            raise ValueError("Load a molecular system before setting a Movie baseline.")
        current = self._view.export_state(skip_digestion=True)
        timeline = _MovieTimeline(
            {
                "molsysmovie_version": MOVIE_TIMELINE_VERSION,
                "duration_ms": duration_ms,
                "units": {"time": "ms", "camera_length": "angstrom"},
                "baseline": {"scene": current if state is None else state, "camera": camera, "binding": binding},
                "tracks": [],
            }
        )
        if state is not None:
            timeline.check_binding(binding, current)
        self._install_timeline(timeline)

    @signal(tags=["movie", "capture"])
    @digest()
    async def capture_baseline_async(
        self, duration_ms: float, *, timeout: float = 5.0, skip_digestion: bool = False
    ) -> dict:
        """Start a new track recipe from an acknowledged live scene.

        Capture the primary canvas's actual camera, structure and supported
        background/lighting channels, including during trajectory playback.
        The duration is in milliseconds and the
        timeout in seconds. Success replaces the previous recipe with an empty
        set of tracks and returns its detached dictionary. Failure/cancellation
        preserves the recipe. An active Movie operation must finish first.
        """
        from ._movie_baseline import capture_baseline

        return await capture_baseline(self, duration_ms, timeout=timeout)

    @signal(tags=["movie", "capture"])
    @digest()
    async def reset_async(self, *, timeout: float = 5.0, skip_digestion: bool = False) -> dict:
        """Restore the recorded scene before time-zero keys and await a draw.

        Pause Movie and competing motion, restore the baseline's objects,
        camera, structure and recorded environment, and return the acknowledged
        state. The recipe and scientific system stay unchanged. Later scene
        objects are removed; object changes form one Undo step. Unrecorded
        viewport/export preferences retain ordinary state-import semantics.
        A timeout/cancellation can leave accepted scene changes visible.
        """
        from ._movie_seek import seek_movie

        if self._playback is not None:
            self._require_timeline()
            await self.pause_async(skip_digestion=True)
        return await seek_movie(self, 0, timeout=timeout, reset_baseline=True)

    @signal()
    @digest()
    def set_duration(self, duration_ms: float, *, skip_digestion: bool = False) -> None:
        """Set the duration in milliseconds, preserving keys within the new interval."""
        timeline = self._require_timeline()
        self._install_timeline(timeline.edit(duration=duration_ms, tracks=timeline.track_records()))

    @signal()
    @digest()
    def add_track(self, track: dict, *, skip_digestion: bool = False) -> str:
        """Add a tagged track containing a target, property and ordered keys."""
        timeline = self._require_timeline()
        timeline = timeline.edit(duration=timeline.duration_ms, tracks=[*timeline.track_records(), track])
        timeline.check_binding(self._view._source_state_binding(), self._view.export_state(skip_digestion=True))
        self._install_timeline(timeline)
        return track["tag"]

    @signal()
    @digest()
    def update_track(self, tag: str, *, keys: list, skip_digestion: bool = False) -> None:
        """Replace a track's ordered keys atomically, keeping its target and property."""
        timeline = self._require_timeline()
        tracks = timeline.track_records()
        for track in tracks:
            if track["tag"] == tag:
                track["keys"] = keys
                self._install_timeline(timeline.edit(duration=timeline.duration_ms, tracks=tracks))
                return
        raise KeyError(f"Unknown Movie track {tag!r}.")

    @signal()
    @digest()
    def remove_track(self, tag: str, *, skip_digestion: bool = False) -> None:
        """Remove one scheduled property track without changing the live scene."""
        timeline = self._require_timeline()
        tracks = [track for track in timeline.track_records() if track["tag"] != tag]
        if len(tracks) == timeline.n_tracks:
            raise KeyError(f"Unknown Movie track {tag!r}.")
        self._install_timeline(timeline.edit(duration=timeline.duration_ms, tracks=tracks))

    @signal()
    @digest()
    def validate(self, *, skip_digestion: bool = False) -> None:
        """Check the recipe's binding and untracked serialized scene definition."""
        timeline = self._require_timeline()
        scene = self._view.export_state(skip_digestion=True)
        timeline.check_binding(self._view._source_state_binding(), scene)
        timeline.check_scene(scene)

    @signal(tags=["movie"])
    @digest()
    def review_rebase(self, *, camera: dict | None = None, skip_digestion: bool = False) -> dict:
        """Review a current-scene baseline while preserving every track/key.

        Return a detached change/conflict report and candidate recipe without
        changing the Movie or scene. Keep the old baseline camera by default;
        an explicit pose uses angstroms and dimensionless up. The current Python
        structure becomes the proposed initial structure. Missing/replaced
        targets require explicit repair; no atom or scientific identity is inferred.
        """
        from ._movie_rebase import review_rebase

        return review_rebase(self, camera)

    @signal(tags=["movie"])
    @digest()
    async def review_rebase_async(self, *, timeout: float = 5.0, skip_digestion: bool = False) -> dict:
        """Review an acknowledged camera/frame and supported renderer environment.

        Keep all tracks/keys and leave scene and recipe unchanged. Return an
        explicit proposal for rebase(review). Its observation ticket belongs
        to this View and is superseded by the next successful live review or
        recipe replacement; it is not part of a saved recipe/session.
        """
        from ._movie_rebase import review_rebase_async

        return await review_rebase_async(self, timeout=timeout)

    @signal(tags=["movie"])
    @digest()
    def rebase(self, review: dict, *, skip_digestion: bool = False) -> None:
        """Accept an unchanged current review without applying it to the scene.

        Recheck the original recipe and reviewed scene before replacing the
        baseline. Reject stale/edited reviews and scientific/target conflicts.
        Use reset_async() separately to apply the new recorded scene.
        """
        from ._movie_rebase import rebase

        rebase(self, review)

    @signal(tags=["movie"])
    @digest()
    def review_import(
        self,
        data: dict,
        *,
        target_map: list | None = None,
        structure_index_map: list | None = None,
        camera: dict | None = None,
        skip_digestion: bool = False,
    ) -> dict:
        """Review a version-1 or version-2 recipe against the prepared scene.

        Version-2 target maps contain source/target domain and tag records, within the
        same domain. Structure correspondence is new-to-old, one entry per
        destination structure. Each referenced source frame needs exactly one
        destination. Changed molecular bindings require both explicit maps;
        no molecular, scientific or spatial correspondence is inferred.
        Camera keys keep their angstrom world coordinates; camera optionally
        replaces only the baseline pose. The returned report is detached and
        does not change either the scene or the current Movie. Only the latest
        successful review belongs to this View and can be accepted.

        Version-1 migration admits complete camera/structure channels, safe
        constant-up Cartesian paths and bounded rounded structure sweeps.
        Its untyped visibility sources require explicit domain="legacy" maps
        to tagged scene targets. Camera-free recipes require camera. Unknown
        source binding and initial visibility remain explicit in the report;
        partial channels or unsupported paths produce conflicts.
        """
        from ._movie_import import review_import

        return review_import(self, data, target_map=target_map, structure_index_map=structure_index_map, camera=camera)

    @signal(tags=["movie"])
    @digest()
    def apply_import(self, review: dict, *, skip_digestion: bool = False) -> None:
        """Accept an unchanged current import review without scene commands.

        Reject stale, edited, foreign or conflicted reviews and active Movie
        operations. Preserve the existing recipe on failure. Use reset_async()
        separately when ready to apply the imported baseline to the renderer.
        """
        from ._movie_import import apply_import

        apply_import(self, review)

    @signal()
    @digest()
    def evaluate(self, time_ms: float, *, skip_digestion: bool = False) -> dict:
        """Return detached camera, structure, visibility and tracked appearance at a time in milliseconds."""
        return self._require_timeline().evaluate(time_ms)

    @signal(tags=["movie", "capture"])
    @digest()
    async def seek_async(self, time_ms: float, *, timeout: float = 5.0, skip_digestion: bool = False) -> dict:
        """Apply a version-2 sample and await the primary canvas's completed draw.

        The sample sets the camera, structure and explicitly tracked visibility.
        The method pauses competing motion and returns the evaluated sample once
        the renderer confirms the camera and structure. ``timeout`` is in seconds.
        Cancelling the wait does not undo scene commands already accepted.
        """
        from ._movie_seek import seek_movie

        if self._playback is not None:
            self._require_timeline().evaluate(time_ms, tracked_visibility=True)
            await self.pause_async(skip_digestion=True)
        return await seek_movie(self, time_ms, timeout=timeout)

    @signal(tags=["movie", "capture"])
    @digest()
    async def play_async(
        self, loop: bool = False, start_time_ms: float = 0.0, *, timeout: float = 5.0, skip_digestion: bool = False
    ) -> dict | None:
        """Preview version-2 tracks until completion or pause on the primary canvas.

        The renderer samples its clock after each completed draw. A slow draw
        can skip intermediate times, and the final sample is always applied on
        normal completion. The timeout bounds each draw in seconds. Run as an
        asyncio task to control playback from another notebook cell.
        """
        from ._movie_playback import play_movie

        return await play_movie(self, loop=loop, start_time_ms=start_time_ms, timeout=timeout)

    @signal(tags=["movie", "capture"])
    @digest()
    async def pause_async(self, *, skip_digestion: bool = False) -> dict | None:
        """Pause a version-2 preview and return its last acknowledged sample."""
        from ._movie_playback import pause_movie

        return await pause_movie(self)

    # ── Inspection ────────────────────────────────────────────────────────

    @signal()
    @digest()
    def info(self, *, skip_digestion: bool = False) -> dict:
        """Return a summary of the current timeline.

        Returns
        -------
        dict
            Keys: ``n_keyframes``, ``duration_ms``, ``has_camera``,
            ``has_structure_sweep``, ``has_visibility_transitions``.
        """
        if self._timeline is not None:
            return {
                "version": MOVIE_TIMELINE_VERSION,
                "duration_ms": self.duration_ms,
                "n_tracks": self._timeline.n_tracks,
            }
        return {
            "n_keyframes": len(self._keyframes),
            "duration_ms": self.duration_ms,
            "has_camera": any("camera" in kf for kf in self._keyframes),
            "has_structure_sweep": any("structure_index" in kf for kf in self._keyframes),
            "has_visibility_transitions": any("layer_visibility" in kf for kf in self._keyframes),
        }

    # ── Serialization ─────────────────────────────────────────────────────

    @signal()
    @digest()
    def to_dict(self, *, skip_digestion: bool = False) -> dict:
        """Serialise the timeline to a JSON-compatible plain dict.

        The dict can be edited independently or passed to :meth:`from_dict`
        on another view to restore the timeline.
        """
        if self._timeline is not None:
            return self._timeline.to_dict()
        return {
            "molsysmovie_version": _MOLSYSMOVIE_VERSION,
            "keyframes": self.keyframes,
        }

    @signal()
    @digest()
    def from_dict(self, data: dict, *, skip_digestion: bool = False) -> None:
        """Replace the current timeline with data from a plain dict.

        Parameters
        ----------
        data
            A dict as returned by :meth:`to_dict`. Its nested values are copied.
        """
        version = data.get("molsysmovie_version")
        if version == MOVIE_TIMELINE_VERSION:
            timeline = _MovieTimeline(data)
            timeline.check_binding(self._view._source_state_binding(), self._view.export_state(skip_digestion=True))
            self._install_timeline(timeline)
            return
        if version != _MOLSYSMOVIE_VERSION:
            raise ValueError(f"Unsupported molsysmovie_version={version!r}.")
        keyframes = data.get("keyframes", [])
        for i, kf in enumerate(keyframes):
            if "time_ms" not in kf:
                raise ValueError(f"Keyframe {i} is missing 'time_ms'.")
            if i > 0 and kf["time_ms"] <= keyframes[i - 1]["time_ms"]:
                raise ValueError(
                    f"Keyframe {i} time_ms={kf['time_ms']} is not strictly "
                    f"greater than keyframe {i - 1} time_ms={keyframes[i - 1]['time_ms']}."
                )
        self._keyframes = [deepcopy(dict(kf)) for kf in keyframes]
        self._timeline = None
        self._invalidate_observation()

    @signal()
    @digest()
    def save(self, path: str | Path, *, skip_digestion: bool = False) -> None:
        """Write the timeline to a JSON file.

        Parameters
        ----------
        path
            Output file path (``.json`` extension recommended).
        """
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @signal()
    @digest()
    def load(self, path: str | Path, *, skip_digestion: bool = False) -> None:
        """Replace the timeline from a JSON file written by :meth:`save`.

        Parameters
        ----------
        path
            Path to a JSON file.
        """
        self.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # ── Playback / export (Phase 2 / Phase 3) ─────────────────────────────

    @signal()
    @digest()
    def play(self, loop: bool = False, start_time_ms: float = 0.0, *, skip_digestion: bool = False) -> None:
        """Preview the movie in the browser.

        Sends the current timeline to the frontend and starts
        ``requestAnimationFrame``-driven playback. The ``movie_playback_done``
        event is emitted when a non-looping animation finishes.

        Parameters
        ----------
        loop
            If ``True``, the animation repeats indefinitely.
        start_time_ms
            Time offset in milliseconds to start the playback from.
            Defaults to ``0.0``.
        """
        self._validate_ready()
        start_time_ms = float(start_time_ms)
        if start_time_ms < 0.0:
            raise ValueError("start_time_ms must be positive or zero.")
        if self._keyframes and start_time_ms > self.duration_ms:
            raise ValueError(
                f"start_time_ms={start_time_ms} cannot be greater than movie duration={self.duration_ms} ms."
            )

        self._view._send_runtime_only(  # noqa: SLF001
            {
                "op": "play_movie",
                "keyframes": list(self._keyframes),
                "loop": bool(loop),
                "start_time_ms": start_time_ms,
            }
        )

    @signal()
    @digest()
    def stop(self, *, skip_digestion: bool = False) -> None:
        """Stop browser playback."""
        if self._playback is not None:
            self._playback.pause_requested = True
            return
        self._view._send_runtime_only({"op": "stop_movie"})  # noqa: SLF001

    @signal()
    @digest()
    def export(
        self,
        path: str | Path,
        *,
        fps: int = 25,
        width_px: int | None = None,
        height_px: int | None = None,
        format: str | None = None,
        timeout_s: float | None = None,
        skip_digestion: bool = False,
    ) -> Path:
        """Export the movie to a video file.

        Renders each frame in the browser (tick-by-tick, no wall clock) and
        stitches the PNG frames into a video with ``imageio[ffmpeg]``.

        Parameters
        ----------
        path
            Output file path.  Format is inferred from the extension
            (``.mp4``, ``.gif``, ``.webm``).  ``format`` overrides this.
        fps
            Frames per second.
        width_px, height_px
            Output resolution.  Defaults to the current canvas size.
        format
            Explicit format string (``"mp4"``, ``"gif"``, ``"webm"``).
        timeout_s
            Maximum seconds to wait for all frames.  Defaults to
            ``max(60, duration_ms/1000 × 10 + 30)``.

        Returns
        -------
        Path
            Absolute path to the written file.
        """
        try:
            # `imageio.v2` on purpose: the bare module's `imread` warns that v3 will change
            # its behaviour, and this code wants the v2 semantics it was written against.
            import imageio.v2 as imageio  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "imageio is required for movie export. Install with: pip install imageio[ffmpeg]"
            ) from exc

        self._validate_ready()
        fps = int(fps)
        path = Path(path).resolve()

        if not getattr(self._view, "_ready", False):
            import os

            if os.environ.get("MSM_VIEWS_FROM_HTML_FILES") == "True":
                # No live frontend is connected (e.g. running headlessly via nbconvert or doc build).
                # Write a placeholder black video/GIF to the requested path to avoid blocking.
                path.parent.mkdir(parents=True, exist_ok=True)
                import numpy as np

                dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
                imageio.mimwrite(str(path), [dummy_img], **_frame_rate_kwargs(path, fps))
                return path

        total_frames = int(self.duration_ms / 1000.0 * fps) + 1
        if timeout_s is None:
            timeout_s = max(60.0, self.duration_ms / 1000.0 * 10 + 30.0)

        view = self._view  # noqa: SLF001
        view._movie_export_frames = []  # type: ignore[attr-defined]
        view._movie_export_done = False  # type: ignore[attr-defined]

        payload: dict = {
            "op": "play_movie",
            "mode": "export",
            "keyframes": list(self._keyframes),
            "fps": fps,
            "total_frames": total_frames,
        }
        if width_px is not None:
            payload["width_px"] = int(width_px)
        if height_px is not None:
            payload["height_px"] = int(height_px)
        view._send_runtime_only(payload)  # type: ignore[attr-defined]

        # Cooperative wait: under a Qt host the movie frames arrive as events that
        # must be processed on this same (main) thread, so a plain time.sleep would
        # deadlock. If the host exposes an event pump (view._qt_process_events, set
        # to QCoreApplication.processEvents), drive it while waiting. In Jupyter /
        # non-Qt backends there is no pump and this degrades to the sleep loop.
        process_events = getattr(view, "_qt_process_events", None)  # noqa: SLF001
        deadline = time.monotonic() + timeout_s
        while not view._movie_export_done:  # type: ignore[attr-defined]
            if time.monotonic() > deadline:
                received = len(view._movie_export_frames or [])  # type: ignore[attr-defined]
                view._movie_export_frames = None  # type: ignore[attr-defined]
                raise TimeoutError(
                    f"Movie export timed out after {timeout_s:.0f}s (received {received} of {total_frames} frames)."
                )
            if callable(process_events):
                try:
                    process_events()
                except Exception:
                    pass
            time.sleep(0.05)

        frames_data = view._movie_export_frames  # type: ignore[attr-defined]
        view._movie_export_frames = None  # type: ignore[attr-defined]
        view._movie_export_done = False  # type: ignore[attr-defined]

        imgs = [_decode_frame(f["data_uri"]) for f in frames_data]
        imageio.mimwrite(str(path), imgs, **_frame_rate_kwargs(path, fps))
        return path

    @signal(tags=["movie", "export"])
    @digest()
    async def export_async(
        self,
        path: str | Path,
        *,
        fps: int | float | str = 25,
        width_px: int = 1280,
        height_px: int = 720,
        sample_level: int = 2,
        format: str | None = None,
        overwrite: bool = False,
        include_overlays: bool = True,
        timeout: float = 15.0,
        on_progress=None,
        skip_digestion: bool = False,
    ) -> dict:
        """Render a version-2 Movie to MP4, WebM or a lossless PNG ZIP.

        Samples the half-open interval at a constant rational ``fps`` (for
        example ``"30000/1001"``). The live primary canvas must support Movie
        frame capture. One frame is rendered and encoded at a time; the
        destination is published only after successful encoder completion.
        ``sample_level`` selects Mol* multisampling (0–5; default 2). It affects
        exported images only and is recorded in the manifest. ``timeout``
        bounds renderer/encoder waits and must be in (0, 300] seconds. Cancel the await
        task to stop export. Competing Movie operations are refused.

        Returns the absolute ``path``, output ``bytes`` and detached
        ``manifest`` (recipe, sampling, composition and encoder). The manifest
        is also embedded in video metadata or the PNG archive. Native geometry
        annotations are included. Visible trajectory plots currently require
        hiding or the explicit ``include_overlays=False`` exclusion.

        ``on_progress`` is an optional synchronous callback receiving a detached
        progress dictionary. The view remains at the last sampled pose.
        MP4/WebM require the optional imageio-ffmpeg backend; all formats require
        ImageIO. A missing renderer or codec never produces a placeholder.
        """
        from ._movie_export import export_movie

        return await export_movie(
            self,
            path,
            fps=fps,
            width_px=width_px,
            height_px=height_px,
            sample_level=sample_level,
            format=format,
            overwrite=overwrite,
            include_overlays=include_overlays,
            timeout=timeout,
            on_progress=on_progress,
        )

    # ── Internal ──────────────────────────────────────────────────────────

    def _validate_ready(self) -> None:
        self._legacy_only()
        if len(self._keyframes) < 2:
            raise ValueError(f"Timeline needs at least 2 keyframes; has {len(self._keyframes)}.")

    def _legacy_only(self) -> None:
        if self._timeline is not None:
            raise ValueError("This operation uses version-1 keyframes. Version-2 tracks support headless evaluation.")

    def _require_timeline(self) -> _MovieTimeline:
        if self._timeline is None:
            raise ValueError("Set a Movie baseline before using tracks.")
        self._timeline.check_binding(self._view._source_state_binding())
        return self._timeline

    def _install_timeline(self, timeline: _MovieTimeline) -> None:
        self._keyframes = []
        self._timeline = timeline
        self._invalidate_observation()

    def _invalidate_observation(self) -> None:
        """Release a stale live review, including its reference to molecular data."""
        self._rebase_capture = None
        self._import_review = None
        self._studio_revision += 1
        if self._studio is not None:
            self._studio.publish()

    def _studio_owner(self):
        if self._studio is None:
            from ._movie_studio import MovieStudio

            self._studio = MovieStudio(self)
        return self._studio

    def _studio_runtime_changed(self):
        if self._studio is not None:
            self._studio.publish()

    def _session_recipe(self, state):
        if self._timeline is None:
            return None
        timeline = self._require_timeline()
        timeline.check_binding(self._view._source_state_binding(), state)
        return timeline.to_dict()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _frame_rate_kwargs(path: Path, fps: int) -> dict:
    """The frame-rate argument each writer actually accepts.

    Pillow, which writes the GIFs, dropped `fps` for `duration` in milliseconds per frame
    and warns on every call that still passes it. The video writers kept `fps`. Choosing by
    suffix is what keeps both quiet and correct; passing `fps` to both is what produced a
    deprecation warning on every GIF export.
    """
    if path.suffix.lower() == ".gif":
        return {"duration": 1000.0 / float(fps)}
    return {"fps": fps}


def _decode_frame(data_uri: str):
    """Decode a ``data:image/png;base64,...`` string to a numpy array via imageio."""
    import imageio.v2 as imageio  # type: ignore[import]

    _, encoded = data_uri.split(",", 1)
    return imageio.imread(io.BytesIO(base64.b64decode(encoded)))


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _validate_camera_snapshot(snap: dict) -> None:
    for key in ("position", "target", "up"):
        if key not in snap:
            raise ValueError(
                f"Camera snapshot missing required key '{key}'. "
                "Use view.camera.get_snapshot() to obtain a valid snapshot."
            )
        val = snap[key]
        if not (hasattr(val, "__len__") and len(val) == 3):
            raise ValueError(f"Camera snapshot key '{key}' must be a sequence of 3 numbers, got {val!r}.")
