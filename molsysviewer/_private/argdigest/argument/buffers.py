from ...exceptions import ArgumentError


def digest_buffers(buffers, caller=None):
    if buffers is None:
        return None
    if isinstance(buffers, (list, tuple)) and all(isinstance(item, (bytes, bytearray, memoryview)) for item in buffers):
        return buffers
    raise ArgumentError("buffers", value=buffers, caller=caller)
