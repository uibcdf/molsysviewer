from ...exceptions import ArgumentError


def digest_layer(layer, caller=None):
    """Digest a layer reference: its tag, a ``Layer`` object, or ``None``.

    ``None`` means "no layer" (it detaches the object from its current layer).
    A string is returned stripped; an object exposing a ``tag`` attribute is
    passed through so the caller can read the tag from it.
    """
    if layer is None:
        return None

    if isinstance(layer, str):
        normalized = layer.strip()
        if normalized:
            return normalized
    elif hasattr(layer, "tag"):
        return layer

    raise ArgumentError("layer", value=layer, caller=caller, message=None)
