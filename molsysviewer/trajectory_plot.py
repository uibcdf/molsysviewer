from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from smonitor import signal

from molsysviewer.colors import colors as _color_registry
from molsysviewer.colors import normalize_color


def _is_sequence(value: Any) -> bool:
    # NumPy arrays are not `collections.abc.Sequence`, but per-frame data in this
    # ecosystem (RMSD, radius of gyration, an energy term, coordinates out of
    # MolSysMT) arrives as arrays, so rejecting them forced a manual `.tolist()`.
    if isinstance(value, np.ndarray):
        return value.ndim >= 1
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


class TrajectoryPlotManager:
    """Synchronized 2D trajectory plot linked to the 3D molecular frame.

    A generic viewer primitive with no addon dependency: push one or more
    per-frame scalar series (RMSD, radius of gyration, a channel bottleneck
    radius, an energy term, ...) and the viewer renders a 2D plot overlay whose
    playhead marker stays synced to the current trajectory frame. Clicking or
    hovering a point in the plot sets the corresponding molecular frame.

    The last plot state is recorded as part of the scene "look", so it is
    reproduced on rebuild and preserved on export, exactly like the legend and
    focus-fade overlays.
    """

    def __init__(self, view: Any) -> None:
        self._view = view

    # -- normalization helpers ------------------------------------------------

    @staticmethod
    def _normalize_series(series: Any) -> list[dict[str, Any]]:
        """Return an ordered list of ``{"label", "values"}`` dicts.

        Accepts a single sequence of numbers, a mapping ``{label: sequence}``,
        or a list of sequences.
        """
        if isinstance(series, Mapping):
            items = list(series.items())
        elif _is_sequence(series) and len(series) > 0 and all(_is_sequence(s) for s in series):
            items = [(f"series {i + 1}", s) for i, s in enumerate(series)]
        elif _is_sequence(series):
            items = [("series 1", series)]
        else:
            raise ValueError("series must be a sequence of numbers, a mapping, or a list of sequences")

        out: list[dict[str, Any]] = []
        length: int | None = None
        for label, values in items:
            if not _is_sequence(values):
                raise ValueError(f"series {label!r} must be a sequence of numbers")
            floats = [float(v) for v in values]
            if length is None:
                length = len(floats)
            elif len(floats) != length:
                raise ValueError(
                    f"all series must have the same length; {label!r} has {len(floats)}, expected {length}"
                )
            out.append({"label": str(label), "values": floats})
        if length in (None, 0):
            raise ValueError("series must contain at least one value per frame")
        return out

    def _resolve_series_colors(self, series: list[dict[str, Any]], colors: Any) -> None:
        """Attach an integer ``color`` to each series in place, if provided.

        ``colors`` may be an explicit list of colors (one per series) or the
        name of a registered palette/scheme (e.g. a CVD-safe scheme like
        ``"okabe_ito"``), in which case series are coloured in palette order.
        """
        if colors is None:
            return
        if isinstance(colors, str):
            labels = [s["label"] for s in series]
            scheme = _color_registry.get_scheme(colors, categories=labels)
            for s in series:
                s["color"] = scheme.mapping[s["label"]]
            return
        if _is_sequence(colors):
            if len(colors) != len(series):
                raise ValueError(f"expected {len(series)} colors, got {len(colors)}")
            for s, c in zip(series, colors):
                s["color"] = normalize_color(c)
            return
        raise ValueError("colors must be a list of colors or a registered palette/scheme name")

    @staticmethod
    def _normalize_events(events: Any, n_frames: int) -> list[dict[str, Any]]:
        if events is None:
            return []
        if not _is_sequence(events):
            raise ValueError("events must be a sequence of {frame, ...} entries")
        out: list[dict[str, Any]] = []
        for entry in events:
            if not isinstance(entry, Mapping) or "frame" not in entry:
                raise ValueError("each event must be a mapping with at least a 'frame' key")
            frame = int(entry["frame"])
            if not 0 <= frame < n_frames:
                raise ValueError(f"event frame {frame} is out of range [0, {n_frames})")
            event: dict[str, Any] = {"frame": frame}
            if entry.get("label") is not None:
                event["label"] = str(entry["label"])
            if entry.get("color") is not None:
                event["color"] = normalize_color(entry["color"])
            out.append(event)
        return out

    # -- public API -----------------------------------------------------------

    @signal(tags=["trajectory", "plot"])
    def show(
        self,
        series: Any,
        *,
        x: Sequence[float] | None = None,
        colors: Any = None,
        events: Any = None,
        x_label: str | None = None,
        y_label: str | None = None,
        title: str | None = None,
    ) -> None:
        """Show (or replace) the synchronized 2D trajectory plot.

        Parameters
        ----------
        series
            Per-frame scalar data: a single sequence, a mapping
            ``{label: sequence}``, or a list of sequences. All series must have
            the same length (one value per frame).
        x
            Optional x-axis values (defaults to frame indices ``0..n-1``).
        colors
            Per-series colors, or the name of a registered palette/scheme
            (e.g. the CVD-safe ``"okabe_ito"``) to colour series in order.
        events
            Optional vertical event markers: a list of ``{"frame", "label"?,
            "color"?}`` mappings.
        x_label, y_label, title
            Optional axis and plot labels.
        """
        normalized = self._normalize_series(series)
        n_frames = len(normalized[0]["values"])
        self._resolve_series_colors(normalized, colors)

        x_values: list[float] | None = None
        if x is not None:
            if not _is_sequence(x):
                raise ValueError("x must be a sequence of numbers")
            x_values = [float(v) for v in x]
            if len(x_values) != n_frames:
                raise ValueError(f"x must have {n_frames} values, got {len(x_values)}")

        options: dict[str, Any] = {
            "visible": True,
            "series": normalized,
            "n_frames": n_frames,
            "events": self._normalize_events(events, n_frames),
        }
        if x_values is not None:
            options["x"] = x_values
        if x_label is not None:
            options["x_label"] = str(x_label)
        if y_label is not None:
            options["y_label"] = str(y_label)
        if title is not None:
            options["title"] = str(title)

        self._view._send({"op": "set_trajectory_plot", "options": options})

    # ``update`` is a semantic alias: pushing a new state replaces the old one.
    update = show

    @signal(tags=["trajectory", "plot"])
    def clear(self) -> None:
        """Hide and clear the trajectory plot overlay."""
        self._view._send({"op": "set_trajectory_plot", "options": {"visible": False}})

    hide = clear


__all__ = ["TrajectoryPlotManager"]
