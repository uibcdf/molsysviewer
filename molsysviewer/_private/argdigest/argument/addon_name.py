"""`addon_name` identifies a registered add-on when resolving one of its panel widgets.

A non-empty string. It is not checked against the registry: `resolve_panel_widget` is
called from the frontend routing path, where an add-on may legitimately have been disabled
between the request being sent and it arriving, and refusing here would turn a routine
race into an argument error.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_addon_name(addon_name, caller=None):
    if isinstance(addon_name, str) and addon_name.strip():
        return addon_name
    raise ArgumentError("addon_name", value=addon_name, caller=caller,
                        message="expected the name an add-on is registered under")
