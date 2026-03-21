from __future__ import annotations

from pathlib import Path
from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest
from .figures import FigureSpec


def _export_html_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    def value(index: int, name: str) -> Any:
        if name in kwargs:
            return kwargs[name]
        if len(args) > index:
            return args[index]
        return None

    return {
        "output_filename": value(1, "output_filename"),
        "mode": value(5, "mode"),
        "include_popout": value(4, "include_popout"),
    }


class ExportManager:
    """Public export namespace for HTML and image outputs."""

    def __init__(self, view: Any) -> None:
        self._view = view

    @signal(tags=["export", "html"], extra_factory=_export_html_signal_extra)
    @digest()
    def html(
        self,
        output_filename: str,
        *,
        title: str = "MolSysViewer",
        include_controls: bool = True,
        include_popout: bool = True,
        mode: str = "standalone",
        inline_messages: bool = True,
        skip_digestion: bool = False,
    ) -> None:
        """Export the current viewer scene to an HTML file."""
        self._view._write_html_impl(  # noqa: SLF001
            output_filename,
            title=title,
            include_controls=include_controls,
            include_popout=include_popout,
            mode=mode,
            inline_messages=inline_messages,
        )

    @signal(tags=["export", "image"])
    @digest()
    def image(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        preset: str = "current",
        camera_snapshot: dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export the current viewer scene as a PNG image file."""
        self._view._export_image_impl(  # noqa: SLF001
            output_filename,
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            transparent=transparent,
            preset=preset,
            camera_snapshot=camera_snapshot,
        )

    @signal(tags=["export", "figure"])
    @digest()
    def figure(
        self,
        output_filename: str,
        *,
        figure_spec: FigureSpec | dict[str, Any] | None = None,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 2.0,
        background: str = "white",
        preset: str = "publication-light",
        camera_snapshot: dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export a first figure-oriented PNG using stronger defaults than raw image export."""
        resolved_width_px = width_px
        resolved_height_px = height_px
        resolved_scale = scale
        resolved_background = background
        resolved_preset = preset
        resolved_camera_snapshot = camera_snapshot

        if figure_spec is not None:
            resolved_width_px = width_px if width_px is not None else figure_spec.width_px
            resolved_height_px = height_px if height_px is not None else figure_spec.height_px
            resolved_scale = scale if scale != 2.0 else figure_spec.scale
            resolved_background = background if background != "white" else figure_spec.background
            resolved_preset = preset if preset != "publication-light" else figure_spec.preset
            resolved_camera_snapshot = camera_snapshot if camera_snapshot is not None else figure_spec.camera_snapshot

        self._view._export_figure_impl(  # noqa: SLF001
            output_filename,
            width_px=resolved_width_px,
            height_px=resolved_height_px,
            scale=resolved_scale,
            background=resolved_background,
            preset=resolved_preset,
            camera_snapshot=resolved_camera_snapshot,
        )

    @signal(tags=["export", "figure"])
    @digest()
    def figure_variants(
        self,
        output_directory: str,
        *,
        variants: dict[str, FigureSpec],
        stem: str = "figure",
        skip_digestion: bool = False,
    ) -> list[str]:
        """Export a batch of named figure recipes into one directory.

        This is intentionally narrow: callers should derive concrete
        `FigureSpec` objects first, typically from a shared base recipe.
        """
        outdir = Path(output_directory)
        outdir.mkdir(parents=True, exist_ok=True)

        written: list[str] = []
        for name, spec in variants.items():
            slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-") or "variant"
            output_filename = outdir / f"{stem}-{slug}.png"
            self.figure(
                str(output_filename),
                figure_spec=spec,
                skip_digestion=True,
            )
            written.append(str(output_filename))
        return written
