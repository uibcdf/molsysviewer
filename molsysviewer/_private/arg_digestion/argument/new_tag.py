from ...exceptions import ArgumentError


def digest_new_tag(new_tag, caller=None):
    if isinstance(new_tag, str):
        return new_tag
    raise ArgumentError("new_tag", value=new_tag, caller=caller, message=None)
