from ...exceptions import ArgumentError


def digest_scheme(scheme, caller=None):
    """Digest a structural color-theme name for ``set_color_scheme``.

    Accepts a non-empty ``str`` (a Mol* color-theme name such as ``"chain-id"``,
    ``"residue-name"``, ``"element-symbol"`` or ``"secondary-structure"``),
    returned stripped. Rejects ``None``, empty or whitespace-only strings, and
    non-string values — matching the non-empty requirement the public method
    enforces internally.
    """
    if isinstance(scheme, str):
        normalized = scheme.strip()
        if normalized:
            return normalized

    raise ArgumentError("scheme", value=scheme, caller=caller, message=None)
