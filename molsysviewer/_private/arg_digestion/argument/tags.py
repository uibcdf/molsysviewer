from ...exceptions import ArgumentError


def digest_tags(tags, caller=None):
    if tags is None:
        return None
    if isinstance(tags, str):
        return tags
    if isinstance(tags, (list, tuple)) and all(isinstance(item, str) for item in tags):
        return list(tags)
    raise ArgumentError("tags", value=tags, caller=caller, message=None)
