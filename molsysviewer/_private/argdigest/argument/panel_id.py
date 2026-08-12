"""`panel_id` identifies one panel within an add-on.

A non-empty string, unchecked against the add-on's declared panels for the same reason as
`addon_name`: this is the frontend routing path, and the set of panels can change between
a request being sent and arriving.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_panel_id(panel_id, caller=None):
    if isinstance(panel_id, str) and panel_id.strip():
        return panel_id
    raise ArgumentError("panel_id", value=panel_id, caller=caller,
                        message="expected a panel id declared by the add-on")
