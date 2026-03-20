from __future__ import annotations

from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest


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
        skip_digestion: bool = False,
    ) -> None:
        """Export the current viewer scene as a PNG image file."""
        self._view._export_image_impl(  # noqa: SLF001
            output_filename,
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            transparent=transparent,
        )
