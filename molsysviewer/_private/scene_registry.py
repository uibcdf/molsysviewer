"""Dictionary reads are public; writes must go through the scene lifecycle."""


class SceneRegistry(dict):
    def _reject_mutation(self, *args, **kwargs):
        raise TypeError("Use the scene manager's add, delete, set_tag or clear methods.")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    update = _reject_mutation
    pop = _reject_mutation
    popitem = _reject_mutation
    setdefault = _reject_mutation
    __ior__ = _reject_mutation
