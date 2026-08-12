"""`samples` is how many colours to draw from a continuous palette.

A positive integer. Zero or a negative count produces a palette with no colours, and the
failure surfaces far away: `resolve_scheme` indexes `palette.colors[idx % len(...)]`, so an
empty palette raises `ZeroDivisionError` from inside a colour lookup, naming neither the
palette nor the call that registered it.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_samples(samples, caller=None):
    if isinstance(samples, bool) or not isinstance(samples, int):
        raise ArgumentError("samples", value=samples, caller=caller,
                            message="expected a whole number of palette samples")
    if samples < 1:
        raise ArgumentError(
            "samples",
            value=samples,
            caller=caller,
            message="a palette needs at least one sample",
        )
    return samples
