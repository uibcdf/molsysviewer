from molsysviewer._private.exceptions import ArgumentError


def digest_new_layer_tag(new_layer_tag, caller=None):
    if new_layer_tag is None:
        return None
    if isinstance(new_layer_tag, str):
        return new_layer_tag
    raise ArgumentError("new_layer_tag", value=new_layer_tag, caller=caller, message=None)
