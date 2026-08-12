from ...exceptions import ArgumentError

#: The two callers that receive a scheme *definition* rather than a scheme *name*.
#:
#: `set_color_scheme("element_cpk")` names one that exists; `register_scheme(...)` and
#: `resolve_scheme(...)` are handed the thing itself — a mapping of category to colour, or
#: a `CategoricalColorScheme`. Digesting those against the registry of known names is
#: exactly backwards: it refuses every scheme that is not registered yet, which is all of
#: them at the moment they are registered.
_SCHEME_DEFINING_CALLERS = frozenset({
    "molsysviewer.colors.register_scheme",
    "molsysviewer.colors.resolve_scheme",
    "molsysviewer.colors.ColorRegistry.register_scheme",
    "molsysviewer.colors.ColorRegistry.resolve_scheme",
})


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

    if caller in _SCHEME_DEFINING_CALLERS:
        # A definition, not a name. What makes it a *valid* definition is the registry's
        # own business, and `resolve_scheme` already refuses what it cannot build.
        return scheme

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
