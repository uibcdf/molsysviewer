from ...exceptions import ArgumentError


def digest_inline_messages(inline_messages, caller=None):
    if isinstance(inline_messages, bool):
        return inline_messages
    raise ArgumentError("inline_messages", value=inline_messages, caller=caller, message=None)
