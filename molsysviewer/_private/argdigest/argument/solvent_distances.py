from ...exceptions import ArgumentError


def digest_solvent_distances(solvent_distances, caller=None):
    if solvent_distances is None:
        return None
    if isinstance(solvent_distances, (list, tuple)):
        if all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in solvent_distances):
            return [float(item) for item in solvent_distances]
    raise ArgumentError("solvent_distances", value=solvent_distances, caller=caller, message=None)
