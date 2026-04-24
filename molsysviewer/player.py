from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from ._private.arg_digestion import digest


class PlayerManager:
    """Manages playback and frame navigation for multi-structure systems.

    Access via ``view.player``.

    Read-only state
    ---------------
    index          Current frame index (0-based).
    n_structures   Total number of structures (frames) in the loaded system.
    is_playing     Whether playback is active (Python-side tracking).

    Mutable defaults (changed with ``set_*`` methods)
    --------------------------------------------------
    fps            Frames per second used by :meth:`play`.
    step_size      Frames advanced per tick used by :meth:`play`.
    mode           Playback mode: ``"loop"``, ``"once"``, ``"ping-pong"``.
    direction      Playback direction: ``"forward"`` or ``"backward"``.
    """

    def __init__(self, view: Any) -> None:
        self._view = view
        self._fps: int = 30
        self._step_size: int = 1
        self._mode: str = "loop"
        self._direction: str = "forward"
        self._is_playing: bool = False

    # ── Read-only state ────────────────────────────────────────────────────

    @property
    def index(self) -> int:
        """Current frame index (0-based)."""
        return self._view._current_structure_index  # noqa: SLF001

    @property
    def n_structures(self) -> int:
        """Total number of structures (frames) in the loaded molecular system."""
        molsys = self._view._molsys  # noqa: SLF001
        if molsys is None:
            return 0
        try:
            return int(msm.get(molsys, element="system", n_structures=True, skip_digestion=True))
        except Exception:
            return 0

    @property
    def is_playing(self) -> bool:
        """True while playback is active (Python-side tracking)."""
        return self._is_playing

    # ── Mutable defaults ───────────────────────────────────────────────────

    @property
    def fps(self) -> int:
        return self._fps

    @property
    def step_size(self) -> int:
        return self._step_size

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def direction(self) -> str:
        return self._direction

    # ── Navigation ─────────────────────────────────────────────────────────

    @signal(tags=["structures"])
    @digest()
    def go_to_structure(self, index: int, skip_digestion: bool = False) -> None:
        """Jump to a specific frame index.

        Parameters
        ----------
        index
            Zero-based frame index to display.
        """
        self._view._send({"op": "set_trajectory_frame", "index": int(index)})  # noqa: SLF001
        self._view._current_structure_index = int(index)  # noqa: SLF001
        # NPT: auto-update box when box is visible
        box_record = getattr(self._view, "_box_record", None)  # noqa: SLF001
        if box_record is not None:
            self._view.show_box(  # noqa: SLF001
                color=box_record["color"],
                width=box_record["width"],
                alpha=box_record["alpha"],
                structure_indices=int(index),
                skip_digestion=True,
            )

    @signal(tags=["structures"])
    @digest()
    def go_to_first(self, skip_digestion: bool = False) -> None:
        """Jump to the first structure (index 0)."""
        self.go_to_structure(0, skip_digestion=True)

    @signal(tags=["structures"])
    @digest()
    def go_to_last(self, skip_digestion: bool = False) -> None:
        """Jump to the last structure."""
        n = self.n_structures
        if n > 0:
            self.go_to_structure(n - 1, skip_digestion=True)

    @signal(tags=["structures"])
    @digest()
    def step_forward(self, n: int = 1, skip_digestion: bool = False) -> None:
        """Advance *n* frames forward (wraps at the end)."""
        total = self.n_structures
        if total == 0:
            return
        new_index = (self.index + int(n)) % total
        self.go_to_structure(new_index, skip_digestion=True)

    @signal(tags=["structures"])
    @digest()
    def step_backward(self, n: int = 1, skip_digestion: bool = False) -> None:
        """Move *n* frames backward (wraps at the beginning)."""
        total = self.n_structures
        if total == 0:
            return
        new_index = (self.index - int(n)) % total
        self.go_to_structure(new_index, skip_digestion=True)

    # ── Playback ───────────────────────────────────────────────────────────

    @signal(tags=["structures"])
    @digest()
    def play(
        self,
        fps: int | None = None,
        mode: str | None = None,
        direction: str | None = None,
        step_size: int | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Start playback through structures.

        Parameters default to the stored values (``navigation.fps``,
        ``navigation.mode``, etc.).  Passing a value here also updates the
        stored default.

        Parameters
        ----------
        fps
            Structures per second.
        mode
            ``"loop"``, ``"once"``, or ``"ping-pong"``.
        direction
            ``"forward"`` or ``"backward"``.
        step_size
            Number of structures to advance per tick.
        """
        if fps is not None:
            self._fps = int(fps)
        if mode is not None:
            self._mode = str(mode)
        if direction is not None:
            self._direction = str(direction)
        if step_size is not None:
            self._step_size = int(step_size)

        self._view._send({  # noqa: SLF001
            "op": "set_trajectory_playback",
            "action": "play",
            "fps": self._fps,
            "mode": self._mode,
            "direction": self._direction,
            "step": self._step_size,
        })
        self._is_playing = True

    @signal(tags=["structures"])
    @digest()
    def pause(self, skip_digestion: bool = False) -> None:
        """Pause playback."""
        self._view._send({"op": "set_trajectory_playback", "action": "stop"})  # noqa: SLF001
        self._is_playing = False

    # ── Setters ────────────────────────────────────────────────────────────

    @signal(tags=["structures"])
    @digest()
    def set_fps(self, fps: int, skip_digestion: bool = False) -> None:
        """Update the playback frame rate.

        If playback is active the new rate takes effect immediately.
        """
        self._fps = int(fps)
        self._view._send({"op": "set_trajectory_playback", "fps": self._fps})  # noqa: SLF001

    @signal(tags=["structures"])
    @digest()
    def set_step_size(self, step_size: int, skip_digestion: bool = False) -> None:
        """Update the number of frames to advance per tick.

        If playback is active, :meth:`play` must be called again for the new
        value to take effect.
        """
        self._step_size = int(step_size)

    @signal(tags=["structures"])
    @digest()
    def set_mode(self, mode: str, skip_digestion: bool = False) -> None:
        """Set the playback mode (``"loop"``, ``"once"``, ``"ping-pong"``)."""
        self._mode = str(mode)

    @signal(tags=["structures"])
    @digest()
    def set_direction(self, direction: str, skip_digestion: bool = False) -> None:
        """Set the playback direction (``"forward"`` or ``"backward"``)."""
        self._direction = str(direction)


__all__ = ["PlayerManager"]
