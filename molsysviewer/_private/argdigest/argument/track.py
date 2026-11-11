from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_track(track, caller=None):
    if isinstance(track, Mapping):
        return track
    raise ArgumentError("track", value=track, caller=caller, message="expected a Movie track mapping")
