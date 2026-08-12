from ...exceptions import ArgumentError


def digest_title(title, caller=None):
    # Optional wherever it labels something that reads fine unlabelled; a plot
    # card and an exported page both default to None.
    if title is None:
        return None
    if isinstance(title, str):
        return title
    raise ArgumentError("title", value=title, caller=caller, message=None)
