from .helpers import digest_selection_and_syntax, digest_selection_inputs


def digest(*args, **kwargs):
    """Lazily import the full digestion registry to avoid eager module loading."""
    from .digest import digest as _digest

    globals()["digest"] = _digest
    return _digest(*args, **kwargs)


__all__ = ["digest", "digest_selection_and_syntax", "digest_selection_inputs"]
