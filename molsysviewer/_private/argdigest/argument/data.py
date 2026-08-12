"""`data` is a serialised movie timeline handed to `from_dict`.

A mapping only. What makes it a *valid* timeline — `molsysmovie_version`, keyframes in
order — stays in `from_dict`, which owns the schema and already refuses a version it does
not know.

The check earns its place on the confusion the API invites: `movie.load(path)` sits beside
`movie.from_dict(data)`, and passing a path here would reach the version lookup as a
string and fail there.
"""

from collections.abc import Mapping

from molsysviewer._private.exceptions import ArgumentError


def digest_data(data, caller=None):
    if isinstance(data, Mapping):
        return data
    raise ArgumentError(
        "data",
        value=data,
        caller=caller,
        message="expected a timeline dict; for a file, use movie.load(path)",
    )
