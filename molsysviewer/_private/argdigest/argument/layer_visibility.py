"""`layer_visibility` is the `{tag: visible}` state a movie keyframe restores.

Tags are strings and visibility is a strict boolean, checked per entry. A truthy value
here would be stored in the timeline and replayed later, so the wrong layer appears in the
exported movie and nothing in the writing session said so — the failure and its cause are
separated by an export.
"""

from collections.abc import Mapping

from molsysviewer._private.exceptions import ArgumentError


def digest_layer_visibility(layer_visibility, caller=None):
    if layer_visibility is None:
        return None
    if not isinstance(layer_visibility, Mapping):
        raise ArgumentError("layer_visibility", value=layer_visibility, caller=caller,
                            message="expected a {tag: visible} mapping")
    for tag, visible in layer_visibility.items():
        if not isinstance(tag, str) or not isinstance(visible, bool):
            raise ArgumentError(
                "layer_visibility",
                value={tag: visible},
                caller=caller,
                message="tags are strings and visibility is True or False",
            )
    return dict(layer_visibility)
