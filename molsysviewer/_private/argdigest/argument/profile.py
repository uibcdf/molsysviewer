"""Validate the profile argument; MolSysMT validates scientific semantics."""

from .._interaction_arguments import digest_text


def digest_profile(profile, caller=None):
    return digest_text(profile, "profile", caller, optional=True)
