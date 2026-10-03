"""Validate the heavy_mode argument; MolSysMT validates scientific semantics."""

from .._interaction_arguments import digest_text


def digest_heavy_mode(heavy_mode, caller=None):
    return digest_text(heavy_mode, "heavy_mode", caller, optional=False)
