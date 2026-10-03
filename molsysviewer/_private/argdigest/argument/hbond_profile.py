"""Validate the hbond_profile argument; MolSysMT validates scientific semantics."""

from .._interaction_arguments import digest_text


def digest_hbond_profile(hbond_profile, caller=None):
    return digest_text(hbond_profile, "hbond_profile", caller, optional=True)
