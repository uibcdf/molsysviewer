from molsysviewer._private.exceptions import ArgumentError


def digest_text(text, caller=None):
    if isinstance(text, str):
        return text
    if text is None:
        raise ArgumentError("text", value=text, caller=caller, message="text cannot be None")
    return str(text)
