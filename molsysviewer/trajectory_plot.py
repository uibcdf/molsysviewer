from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

import numpy as np
from smonitor import signal

from molsysviewer.colors import colors as _color_registry
from molsysviewer.colors import normalize_color

from ._private.argdigest import digest
from ._private.exceptions import ArgumentError


def _is_sequence(value: Any) -> bool:
    if isinstance(value, np.ndarray):
        return value.ndim >= 1
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


class TrajectoryPlotManager:
    """Synchronized 2D trajectory plot cards linked to the 3D molecular frame.

    A generic viewer primitive: push one or more per-frame scalar series (RMSD,
    radius of gyration, a channel bottleneck radius, an energy term, ...) and the
    viewer renders resizable, draggable 2D Data Card overlays whose playhead markers
    stay synced to the current trajectory frame. Clicking or hovering a point in
    a plot seeks the corresponding molecular frame.

    Supports multiple simultaneous cards keyed by tag (defaults to "default").
    """

    def __init__(self, view: Any) -> None:
        self._view = view

    def _cards(self):
        message = self._view._scene_look.get("trajectory_plot", {})
        options = message.get("options", {})
        return deepcopy(options.get("cards", [options] if options.get("series") else []))

    def _validate_cards(self, cards):
        if not isinstance(cards, list):
            raise ArgumentError("series", value=cards)
        tags = set()
        normalized = deepcopy(cards)
        for card in normalized:
            tag = card.get("tag") if isinstance(card, dict) else None
            if not isinstance(tag, str) or not tag.strip() or tag in tags or not isinstance(card.get("visible"), bool):
                raise ArgumentError("tag", value=tag)
            tags.add(tag)
            series = card.get("series")
            if not isinstance(series, list) or not series:
                raise ArgumentError("series", value=series)
            length = None
            for item in series:
                if not isinstance(item, dict) or not isinstance(item.get("label"), str):
                    raise ArgumentError("series", value=series)
                values = item.get("values")
                if not _is_sequence(values) or not len(values):
                    raise ArgumentError("series", value=values)
                item["values"] = self._finite_values(values, "series")
                if length is not None and len(values) != length:
                    raise ArgumentError("series", value=series)
                length = len(values)
                if "color" in item:
                    item["color"] = normalize_color(item["color"])
            if card.get("n_frames") != length:
                raise ArgumentError("series", value=series)
            structures = self._view.player.n_structures
            if self._view.molsys is not None and length != structures:
                raise ArgumentError("series", value=series, message="A trajectory plot requires one value per loaded structure.")
            if "x" in card:
                if not _is_sequence(card["x"]) or len(card["x"]) != length:
                    raise ArgumentError("x", value=card["x"])
                card["x"] = self._finite_values(card["x"], "x")
            card["events"] = self._normalize_events(card.get("events"), length)
        return normalized

    def _replace(self, cards):
        cards = self._validate_cards(cards)
        self._view._send({"op": "set_trajectory_plot", "options": {"cards": cards}})

    def _check_structure_axis(self, n_structures):
        if any(card["n_frames"] != int(n_structures) for card in self._cards()):
            raise ValueError("Clear trajectory plot cards before changing the number of loaded structures.")

    def _prepare_import(self, cards, clear_first, on_conflict):
        incoming = self._validate_cards(cards)
        retained = [] if clear_first else self._cards()
        tags = {card["tag"] for card in retained}
        for card in incoming:
            tag = card["tag"]
            if tag in tags:
                if on_conflict == "raise":
                    raise ValueError(f"Cannot import trajectory plot tag {tag!r}: it already exists.")
                if on_conflict == "skip":
                    continue
                suffix = 2
                while f"{tag}_{suffix}" in tags:
                    suffix += 1
                card["tag"] = f"{tag}_{suffix}"
            tags.add(card["tag"])
            retained.append(card)
        return retained

    @signal(tags=["trajectory", "plot", "query"])
    @digest()
    def records(self, skip_digestion=False):
        """Return detached retained cards, including hidden cards."""
        return self._cards()

    # -- normalization helpers ------------------------------------------------

    @staticmethod
    def _finite_values(values, argument):
        try:
            result = [float(value) for value in values]
        except (TypeError, ValueError, OverflowError) as exc:
            raise ArgumentError(argument, value=values, message="Plot values must be finite numbers.") from exc
        if not all(np.isfinite(value) for value in result):
            raise ArgumentError(argument, value=values, message="Plot values must be finite numbers.")
        return result

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
            floats = TrajectoryPlotManager._finite_values(values, "series")
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
                raise ValueError(f"expected {len(series)} colors, got {len(series)}")
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
    @digest()
    def show(
        self,
        series: Any = None,
        *,
        x: Sequence[float] | None = None,
        colors: Any = None,
        events: Any = None,
        x_label: str | None = None,
        y_label: str | None = None,
        title: str | None = None,
        tag: str = "default",
        width: int | None = None,
        height: int | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Show (or replace) a synchronized 2D trajectory plot card.

        Parameters
        ----------
        series
            Per-frame scalar data: a single sequence, a mapping
            ``{label: sequence}``, or a list of sequences. All series must have
            the same length (one value per loaded structure). ``None`` restores
            the retained card identified by ``tag`` without replacing its data.
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
        tag
            Unique tag identifying the plot card (defaults to ``"default"``).
            Multiple plot cards can be open simultaneously under different tags.
        width, height
            Optional initial width and height in pixels.
        """
        if not isinstance(tag, str) or not tag.strip():
            raise ArgumentError("tag", value=tag)
        cards = self._cards()
        if series is None:
            card = next((item for item in cards if item["tag"] == tag), None)
            if card is None:
                raise KeyError(tag)
            card["visible"] = True
            self._replace(cards)
            return
        normalized = self._normalize_series(series)
        n_frames = len(normalized[0]["values"])
        self._resolve_series_colors(normalized, colors)

        x_values: list[float] | None = None
        if x is not None:
            if not _is_sequence(x):
                raise ValueError("x must be a sequence of numbers")
            x_values = self._finite_values(x, "x")
            if len(x_values) != n_frames:
                raise ValueError(f"x must have {n_frames} values, got {len(x_values)}")

        options: dict[str, Any] = {
            "tag": str(tag),
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
        if width is not None:
            options["width"] = int(width)
        if height is not None:
            options["height"] = int(height)

        cards = [card for card in cards if card["tag"] != tag]
        cards.append(options)
        self._replace(cards)

    # ``update`` is a semantic alias: pushing a new state replaces the old one.
    update = show

    @signal(tags=["trajectory", "plot"])
    @digest()
    def clear(self, tag: str | None = None, *, skip_digestion: bool = False) -> None:
        """Hide and clear trajectory plot cards.

        If ``tag`` is provided, clears that specific card; if ``None``, clears all cards.
        """
        if tag is not None and (not isinstance(tag, str) or not tag.strip()):
            raise ArgumentError("tag", value=tag)
        self._replace([] if tag is None else [card for card in self._cards() if card["tag"] != tag])

    @signal()
    @digest()
    def hide(self, tag: str | None = None, *, skip_digestion: bool = False) -> None:
        """Hide one or all cards, retaining data for ``show(tag=...)``."""
        if tag is not None and (not isinstance(tag, str) or not tag.strip()):
            raise ArgumentError("tag", value=tag)
        cards = self._cards()
        for card in cards:
            if tag is None or card["tag"] == tag:
                card["visible"] = False
        self._replace(cards)


__all__ = ["TrajectoryPlotManager"]
