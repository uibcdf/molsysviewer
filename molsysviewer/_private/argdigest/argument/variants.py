from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.figures import FigureSpec


def digest_variants(variants, caller=None):
    if not isinstance(variants, dict) or len(variants) == 0:
        raise ArgumentError("variants", value=variants, caller=caller, message="Expected a non-empty dictionary.")

    digested = {}
    for key, value in variants.items():
        if not isinstance(key, str) or not key.strip():
            raise ArgumentError("variants", value=variants, caller=caller, message="Variant names must be non-empty strings.")
        if isinstance(value, FigureSpec):
            digested[key.strip()] = value
            continue
        if isinstance(value, dict):
            try:
                digested[key.strip()] = FigureSpec(**value)
            except Exception as exc:  # pragma: no cover - defensive normalization surface
                raise ArgumentError("variants", value=variants, caller=caller, message=str(exc)) from exc
            continue
        raise ArgumentError("variants", value=variants, caller=caller, message="Each variant must be a FigureSpec or dictionary.")
    return digested
