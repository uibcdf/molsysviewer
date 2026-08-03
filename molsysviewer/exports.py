from __future__ import annotations

from collections.abc import Sequence
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


def _export_image_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    def value(index: int, name: str) -> Any:
        if name in kwargs:
            return kwargs[name]
        if len(args) > index:
            return args[index]
        return None

    return {
        "output_filename": value(1, "output_filename"),
        "width_px": value(2, "width_px"),
        "height_px": value(3, "height_px"),
        "transparent": value(5, "transparent"),
        "preset": value(6, "preset"),
    }


def _export_figure_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    def value(index: int, name: str) -> Any:
        if name in kwargs:
            return kwargs[name]
        if len(args) > index:
            return args[index]
        return None

    return {
        "output_filename": value(1, "output_filename"),
        "has_figure_spec": value(2, "figure_spec") is not None,
        "width_px": value(3, "width_px"),
        "height_px": value(4, "height_px"),
        "preset": value(7, "preset"),
    }


def _export_figure_variants_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    def value(index: int, name: str) -> Any:
        if name in kwargs:
            return kwargs[name]
        if len(args) > index:
            return args[index]
        return None

    variants = value(2, "variants") or {}
    return {
        "output_directory": value(1, "output_directory"),
        "stem": value(3, "stem") or "figure",
        "variant_count": len(variants),
    }


def _export_publication_set_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    def value(index: int, name: str) -> Any:
        if name in kwargs:
            return kwargs[name]
        if len(args) > index:
            return args[index]
        return None

    return {
        "output_directory": value(1, "output_directory"),
        "stem": value(3, "stem") or "figure",
        "include_current": value(4, "include_current") or False,
        "has_figure_spec": value(2, "figure_spec") is not None,
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
        runtime: str | Sequence[str] | None = None,
        runtime_assets_dir: str | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export the current viewer scene to an HTML file.

        With ``mode="lite"`` the page loads a shared runtime instead of carrying
        one. ``runtime`` selects where it comes from — by default the runtime
        installed with this package, copied next to the export and addressed by
        relative path, so the result keeps working offline and does not depend on
        a registry entry surviving. See
        ``MolSysView._write_html_impl`` for the full argument documentation.
        """
        self._view._write_html_impl(  # noqa: SLF001
            output_filename,
            title=title,
            include_controls=include_controls,
            include_popout=include_popout,
            mode=mode,
            inline_messages=inline_messages,
            runtime=runtime,
            runtime_assets_dir=runtime_assets_dir,
        )

    @signal(tags=["export", "image"], extra_factory=_export_image_signal_extra)
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

    @signal(tags=["export", "figure"], extra_factory=_export_figure_signal_extra)
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

    @signal(tags=["export", "figure"], extra_factory=_export_figure_variants_signal_extra)
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

    @signal(tags=["export", "figure"], extra_factory=_export_publication_set_signal_extra)
    @digest()
    def figure_publication_set(
        self,
        output_directory: str,
        *,
        figure_spec: FigureSpec | dict[str, Any] | None = None,
        stem: str = "figure",
        include_current: bool = False,
        skip_digestion: bool = False,
    ) -> list[str]:
        """Export the standard publication-oriented figure set to one directory."""
        base = FigureSpec() if figure_spec is None else figure_spec
        variants = base.build_publication_variants(include_current=include_current)
        return self.figure_variants(
            output_directory,
            variants=variants,
            stem=stem,
            skip_digestion=True,
        )
