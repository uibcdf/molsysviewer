"""Validate the selection_mode argument; MolSysMT validates scientific semantics."""

from .._interaction_arguments import digest_text


def digest_selection_mode(selection_mode, caller=None):
    return digest_text(selection_mode, "selection_mode", caller, optional=False)
