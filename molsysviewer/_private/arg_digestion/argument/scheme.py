from ...exceptions import ArgumentError


def digest_scheme(scheme, caller=None):
    """Digest a structural color-scheme name for ``set_color_scheme``.

    Accepts the canonical scheme tags (``chain_default``, ``element_cpk``, …),
    the underlying Mol* theme names (``chain-id``, ``element-symbol``, …), and
    MolSysMT attribute names (``chain_id``, ``group_name``, …). The value is
    resolved to its canonical tag, so a recognized synonym is actually applied
    instead of being silently ignored downstream.

    Unknown names raise ``ArgumentError`` listing the valid options, rather than
    being accepted and quietly doing nothing.
    """
    from ...color_schemes import (
        STRUCTURAL_COLOR_SCHEMES,
        resolve_structural_color_scheme,
    )

    resolved = resolve_structural_color_scheme(scheme)
    if resolved is not None:
        return resolved

    valid = ", ".join(sorted(STRUCTURAL_COLOR_SCHEMES))
    raise ArgumentError(
        "scheme",
        value=scheme,
        caller=caller,
        message=f" Valid color schemes are: {valid}.",
    )
