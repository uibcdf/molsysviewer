"""Validate the hbond_method argument; MolSysMT validates scientific semantics."""

from .._interaction_arguments import digest_text


def digest_hbond_method(hbond_method, caller=None):
    return digest_text(hbond_method, "hbond_method", caller, optional=False)
