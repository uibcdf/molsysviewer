from ...exceptions import ArgumentError


def digest_query_revision(query_revision, caller=None):
    if isinstance(query_revision, str) and query_revision.startswith("sha256:") and len(query_revision) == 71:
        return query_revision
    raise ArgumentError("query_revision", value=query_revision, caller=caller)
