from ...exceptions import ArgumentError


def digest_standards(standards, caller=None):
    if isinstance(standards, str):
        items = [item.strip() for item in standards.split(",") if item.strip()]
        if items:
            return items
    elif isinstance(standards, (list, tuple, set)):
        items = list(standards)
        if all(isinstance(item, str) for item in items):
            return items
    raise ArgumentError("standards", value=standards, caller=caller, message=None)
