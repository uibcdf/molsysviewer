from ...exceptions import ArgumentError


def digest_runtime_urls(runtime_urls, caller=None):
    if runtime_urls is None:
        return None
    if isinstance(runtime_urls, (list, tuple)) and all(isinstance(item, str) for item in runtime_urls):
        return list(runtime_urls)
    raise ArgumentError("runtime_urls", value=runtime_urls, caller=caller)
