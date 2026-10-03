from ...exceptions import ArgumentError


def digest_analysis_revision(analysis_revision, caller=None):
    if isinstance(analysis_revision, str) and analysis_revision.startswith("sha256:") and len(analysis_revision) == 71:
        return analysis_revision
    raise ArgumentError("analysis_revision", value=analysis_revision, caller=caller)
