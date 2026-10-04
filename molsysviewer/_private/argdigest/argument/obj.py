from ...exceptions import ArgumentError


def digest_obj(obj, caller=None):
    from molsysviewer.layers import SceneObject

    if isinstance(obj, SceneObject):
        obj._assert_current()
        return obj
    raise ArgumentError("obj", value=obj, caller=caller)
