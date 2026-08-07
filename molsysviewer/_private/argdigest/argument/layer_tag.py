from molsysviewer._private.exceptions import ArgumentError


def digest_layer_tag(layer_tag, caller=None):
    if layer_tag is None:
        return None
    if isinstance(layer_tag, str):
        return layer_tag
    raise ArgumentError("layer_tag", value=layer_tag, caller=caller, message=None)
