"""Validate the geometry argument; MolSysMT validates scientific semantics."""

from .._interaction_arguments import digest_text


def digest_geometry(geometry, caller=None):
    return digest_text(geometry, "geometry", caller, optional=False)
