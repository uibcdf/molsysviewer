from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.figures import FigureSpec


def digest_figure_spec(figure_spec, caller=None):
    if figure_spec is None:
        return None
    if isinstance(figure_spec, FigureSpec):
        return figure_spec
    if isinstance(figure_spec, dict):
        try:
            return FigureSpec(**figure_spec)
        except Exception as exc:  # pragma: no cover - defensive normalization surface
            raise ArgumentError("figure_spec", value=figure_spec, caller=caller, message=str(exc)) from exc
    raise ArgumentError("figure_spec", value=figure_spec, caller=caller, message=None)
