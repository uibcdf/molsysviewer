from ...exceptions import ArgumentError


def digest_prepare_addons(prepare_addons, caller=None):
    if isinstance(prepare_addons, bool):
        return prepare_addons
    raise ArgumentError("prepare_addons", value=prepare_addons, caller=caller)
