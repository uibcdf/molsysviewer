from ...exceptions import ArgumentError


def digest_obj(obj, caller=None):
    from molsysviewer.layers import SceneObject
    from molsysviewer.regions import Region

    if isinstance(obj, (SceneObject, Region)):
        obj._assert_current()
        return obj
    raise ArgumentError("obj", value=obj, caller=caller)
