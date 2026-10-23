"""
ArgDigest adapter for MolSysViewer.
This module replaces the legacy digestion engine with the standardized ArgDigest framework.
"""

from functools import wraps

from argdigest import arg_digest as _argdigest_digest


def digest(*args, **kwargs):
    """
    MolSysViewer argument digestion decorator.
    Delegates to the external ArgDigest library using the project-specific configuration.
    """
    decorate = _argdigest_digest(config="molsysviewer._argdigest", *args, **kwargs)

    def guarded(function):
        digested = decorate(function)

        @wraps(digested)
        def call(*positional, **keywords):
            from molsysviewer.system_edits import _scene_call_guard

            with _scene_call_guard(positional, keywords, function.__name__):
                return digested(*positional, **keywords)

        return call

    return guarded
