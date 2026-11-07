"""
ArgDigest adapter for MolSysViewer.
This module replaces the legacy digestion engine with the standardized ArgDigest framework.
"""

from functools import wraps
from inspect import iscoroutinefunction

from argdigest import arg_digest as _argdigest_digest


def digest(*args, **kwargs):
    """
    MolSysViewer argument digestion decorator.
    Delegates to the external ArgDigest library using the project-specific configuration.
    """
    decorate = _argdigest_digest(config="molsysviewer._argdigest", *args, **kwargs)

    def guarded(function):
        digested = decorate(function)

        if iscoroutinefunction(function):

            @wraps(digested)
            async def asynchronous_call(*positional, **keywords):
                from molsysviewer.system_edits import _scene_call_guard

                # Digest at entry, but do not retain the thread's molecular
                # edit lock across a kernel yield. Async owners revalidate
                # their captured revisions before committing effects.
                with _scene_call_guard(positional, keywords, function.__name__, function=function):
                    pending = digested(*positional, **keywords)
                return await pending

            return asynchronous_call

        @wraps(digested)
        def call(*positional, **keywords):
            from molsysviewer.system_edits import _scene_call_guard

            with _scene_call_guard(positional, keywords, function.__name__, function=function):
                return digested(*positional, **keywords)

        return call

    return guarded
