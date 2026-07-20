from ...exceptions import ArgumentError


def digest_region(region, caller=None):
    """Digest a region reference: either its tag or a ``Region`` object.

    A string is returned stripped; an object exposing a ``tag`` attribute (a
    ``Region``) is passed through untouched so the caller can use it directly.
    Empty tags and unrelated objects are rejected.
    """
    if isinstance(region, str):
        normalized = region.strip()
        if normalized:
            return normalized
    elif region is not None and hasattr(region, "tag"):
        return region

    raise ArgumentError("region", value=region, caller=caller, message=None)
