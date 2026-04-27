from __future__ import annotations

import base64
import io
import json
import math
import time
from pathlib import Path
from typing import Any

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

    # ── Timeline construction ─────────────────────────────────────────────

    def add_keyframe(
        self,
        time_ms: float,
        *,
        camera: dict | None = None,
        structure_index: int | None = None,
        layer_visibility: dict[str, bool] | None = None,
        easing: str = "linear",
    ) -> None:
        """Add a keyframe to the timeline.

        Parameters
        ----------
        time_ms
            Timestamp in milliseconds. Must be strictly greater than the
            last existing keyframe.
        camera
            Camera snapshot dict with ``position``, ``target``, ``up`` keys
            (all in Å). Use ``view.camera.get_snapshot()`` to capture the
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
        if easing not in _EASING_VALUES:
            raise ValueError(
                f"easing must be one of {sorted(_EASING_VALUES)!r}, got {easing!r}"
            )
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

    def add_visibility_transition(
        self,
        tag: str,
        visible: bool,
        at_time_ms: float,
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

    def add_camera_orbit(
        self,
        duration_ms: float = 5000.0,
        *,
        n_turns: float = 1.0,
        start_time_ms: float | None = None,
        center: list[float] | None = None,
        n_keyframes: int = 36,
        easing: str = "linear",
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
        if easing not in _EASING_VALUES:
            raise ValueError(
                f"easing must be one of {sorted(_EASING_VALUES)!r}, got {easing!r}"
            )
        snap = self._view.camera.get_snapshot(skip_digestion=True)
        if snap is None:
            raise RuntimeError(
                "No camera snapshot available. Load a system first."
            )
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
            raise ValueError(
                "Camera is at the orbit center; cannot determine orbit radius."
            )
        radial_unit = [r / radius for r in radial]

        right = _cross(radial_unit, up)
        right_len = math.sqrt(sum(r * r for r in right))
        if right_len < 1e-9:
            raise ValueError(
                "Camera up vector is parallel to the radial; cannot compute orbit plane."
            )
        right_unit = [r / right_len for r in right]

        if start_time_ms is None:
            start_time_ms = self.duration_ms if self._keyframes else 0.0
        start_time_ms = float(start_time_ms)
        duration_ms = float(duration_ms)

        total_kf = int(n_keyframes * abs(n_turns)) + 1
        for i in range(total_kf):
            t = i / (total_kf - 1) if total_kf > 1 else 0.0
            theta = 2.0 * math.pi * n_turns * t
            new_radial = [
                math.cos(theta) * radial_unit[j] + math.sin(theta) * right_unit[j]
                for j in range(3)
            ]
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

    def add_structure_sweep(
        self,
        *,
        from_index: int = 0,
        to_index: int | None = None,
        start_time_ms: float | None = None,
        duration_ms: float | None = None,
        end_time_ms: float | None = None,
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
        if to_index is None:
            n = self._view.player.n_structures
            if not n:
                raise RuntimeError(
                    "No molecular system loaded; cannot determine to_index. "
                    "Pass to_index explicitly."
                )
            to_index = n - 1

        from_index = int(from_index)
        to_index = int(to_index)
        if from_index > to_index:
            raise ValueError(
                f"from_index ({from_index}) must be ≤ to_index ({to_index})."
            )

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

    def clear(self) -> None:
        """Remove all keyframes and reset the timeline."""
        self._keyframes = []

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def duration_ms(self) -> float:
        """Total duration in milliseconds (0.0 if empty)."""
        return self._keyframes[-1]["time_ms"] if self._keyframes else 0.0

    @property
    def keyframes(self) -> list[dict]:
        """Read-only snapshot of the keyframe list."""
        return list(self._keyframes)

    # ── Inspection ────────────────────────────────────────────────────────

    def info(self) -> dict:
        """Return a summary of the current timeline.

        Returns
        -------
        dict
            Keys: ``n_keyframes``, ``duration_ms``, ``has_camera``,
            ``has_structure_sweep``, ``has_visibility_transitions``.
        """
        return {
            "n_keyframes": len(self._keyframes),
            "duration_ms": self.duration_ms,
            "has_camera": any("camera" in kf for kf in self._keyframes),
            "has_structure_sweep": any(
                "structure_index" in kf for kf in self._keyframes
            ),
            "has_visibility_transitions": any(
                "layer_visibility" in kf for kf in self._keyframes
            ),
        }

    # ── Serialization ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise the timeline to a JSON-compatible plain dict.

        The dict can be passed to :meth:`from_dict` on any view to
        restore the timeline.
        """
        return {
            "molsysmovie_version": _MOLSYSMOVIE_VERSION,
            "keyframes": [dict(kf) for kf in self._keyframes],
        }

    def from_dict(self, data: dict) -> None:
        """Replace the current timeline with data from a plain dict.

        Parameters
        ----------
        data
            A dict as returned by :meth:`to_dict`.
        """
        version = data.get("molsysmovie_version")
        if version != _MOLSYSMOVIE_VERSION:
            raise ValueError(
                f"Unsupported molsysmovie_version={version!r}. "
                f"Expected {_MOLSYSMOVIE_VERSION}."
            )
        keyframes = data.get("keyframes", [])
        for i, kf in enumerate(keyframes):
            if "time_ms" not in kf:
                raise ValueError(f"Keyframe {i} is missing 'time_ms'.")
            if i > 0 and kf["time_ms"] <= keyframes[i - 1]["time_ms"]:
                raise ValueError(
                    f"Keyframe {i} time_ms={kf['time_ms']} is not strictly "
                    f"greater than keyframe {i-1} time_ms={keyframes[i-1]['time_ms']}."
                )
        self._keyframes = [dict(kf) for kf in keyframes]

    def save(self, path: str | Path) -> None:
        """Write the timeline to a JSON file.

        Parameters
        ----------
        path
            Output file path (``.json`` extension recommended).
        """
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        """Replace the timeline from a JSON file written by :meth:`save`.

        Parameters
        ----------
        path
            Path to a JSON file.
        """
        self.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # ── Playback / export (Phase 2 / Phase 3) ─────────────────────────────

    def play(self, loop: bool = False) -> None:
        """Preview the movie in the browser.

        Sends the current timeline to the frontend and starts
        ``requestAnimationFrame``-driven playback. The ``movie_playback_done``
        event is emitted when a non-looping animation finishes.

        Parameters
        ----------
        loop
            If ``True``, the animation repeats indefinitely.
        """
        self._validate_ready()
        self._view._send_runtime_only(  # noqa: SLF001
            {
                "op": "play_movie",
                "keyframes": list(self._keyframes),
                "loop": bool(loop),
            }
        )

    def stop(self) -> None:
        """Stop browser playback."""
        self._view._send_runtime_only({"op": "stop_movie"})  # noqa: SLF001

    def export(
        self,
        path: str | Path,
        *,
        fps: int = 25,
        width_px: int | None = None,
        height_px: int | None = None,
        format: str | None = None,
        timeout_s: float | None = None,
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
            import imageio  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "imageio is required for movie export. "
                "Install with: pip install imageio[ffmpeg]"
            ) from exc

        self._validate_ready()
        fps = int(fps)
        path = Path(path).resolve()

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

        deadline = time.monotonic() + timeout_s
        while not view._movie_export_done:  # type: ignore[attr-defined]
            if time.monotonic() > deadline:
                view._movie_export_frames = None  # type: ignore[attr-defined]
                raise TimeoutError(
                    f"Movie export timed out after {timeout_s:.0f}s "
                    f"(received {len(view._movie_export_frames or [])} of {total_frames} frames)."
                )
            time.sleep(0.05)

        frames_data = view._movie_export_frames  # type: ignore[attr-defined]
        view._movie_export_frames = None  # type: ignore[attr-defined]
        view._movie_export_done = False  # type: ignore[attr-defined]

        imgs = [_decode_frame(f["data_uri"]) for f in frames_data]
        imageio.mimwrite(str(path), imgs, fps=fps)
        return path

    # ── Internal ──────────────────────────────────────────────────────────

    def _validate_ready(self) -> None:
        if len(self._keyframes) < 2:
            raise ValueError(
                f"Timeline needs at least 2 keyframes; has {len(self._keyframes)}."
            )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode_frame(data_uri: str):
    """Decode a ``data:image/png;base64,...`` string to a numpy array via imageio."""
    import imageio  # type: ignore[import]
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
            raise ValueError(
                f"Camera snapshot key '{key}' must be a sequence of 3 numbers, "
                f"got {val!r}."
            )
