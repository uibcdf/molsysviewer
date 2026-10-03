from ...exceptions import ArgumentError


def digest_worker_url(worker_url, caller=None):
    if isinstance(worker_url, str) and worker_url.strip():
        return worker_url
    raise ArgumentError("worker_url", value=worker_url, caller=caller)
