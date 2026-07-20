from ...exceptions import ArgumentError


def digest_color_scheme(color_scheme, caller=None):
    """Digest the ``color_scheme`` representation parameter.

    Same vocabulary as ``scheme``: canonical tags, Mol* theme names, and
    MolSysMT attribute names are resolved to the canonical tag. Unlike
    ``scheme``, unrecognized names are passed through rather than rejected,
    because this parameter is shared with non-structural visuals.
    """
    if color_scheme is None:
        return None

    if isinstance(color_scheme, str):
        from ...color_schemes import resolve_structural_color_scheme

        # Unlike `scheme`, this parameter is shared with non-structural domains
        # (shape and pharmacophore visuals use their own schemes, e.g.
        # `pharmacophore_default`), so unknown names are passed through instead
        # of rejected. Known structural synonyms are still resolved, which is
        # what makes `color_scheme="chain-id"` actually apply.
        resolved = resolve_structural_color_scheme(color_scheme)
        return resolved if resolved is not None else color_scheme

    raise ArgumentError("color_scheme", value=color_scheme, caller=caller, message=None)
