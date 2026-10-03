from ...exceptions import ArgumentError


def digest_analysis_name(analysis_name, caller=None):
    if isinstance(analysis_name, str) and analysis_name.strip():
        return analysis_name
    raise ArgumentError("analysis_name", value=analysis_name, caller=caller)
