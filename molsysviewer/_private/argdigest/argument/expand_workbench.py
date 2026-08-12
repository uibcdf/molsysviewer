"""`expand_workbench` chooses whether the reference demo opens its workbench expanded.

A strict boolean: it is a presentation choice with no other meaning, and a truthy value
would be accepted silently as True, which is the opposite of what a caller passing `0`
intends.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_expand_workbench(expand_workbench, caller=None):
    if isinstance(expand_workbench, bool):
        return expand_workbench
    raise ArgumentError("expand_workbench", value=expand_workbench, caller=caller,
                        message="expected True or False")
