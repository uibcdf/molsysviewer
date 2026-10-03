from .coordinates import digest_coordinates


def digest_new_pos(new_pos, caller=None):
    return digest_coordinates(new_pos, caller=caller)
