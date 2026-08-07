"""
ArgDigest adapter for MolSysViewer.
This module replaces the legacy digestion engine with the standardized ArgDigest framework.
"""

from argdigest import arg_digest as _argdigest_digest

def digest(*args, **kwargs):
    """
    MolSysViewer argument digestion decorator.
    Delegates to the external ArgDigest library using the project-specific configuration.
    """
    return _argdigest_digest(config="molsysviewer._argdigest", *args, **kwargs)
