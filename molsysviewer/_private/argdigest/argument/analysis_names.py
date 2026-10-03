from ...exceptions import ArgumentError


def digest_analysis_names(analysis_names, caller=None):
    if analysis_names is None:
        return None
    names = [analysis_names] if isinstance(analysis_names, str) else analysis_names
    if isinstance(names, (list, tuple)) and names and all(isinstance(name, str) and name.strip() for name in names) and len(set(names)) == len(names):
        return list(names)
    raise ArgumentError("analysis_names", value=analysis_names, caller=caller)
