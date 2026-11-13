"""`format` overrides the movie container inferred from the output path.

`None` means "infer it from the suffix", which is what most callers want. When given it
must be one of the three the exporter can write; a fourth would reach the encoder and fail
there, naming the encoder rather than the argument.
"""

from molsysviewer._private.exceptions import ArgumentError

MOVIE_FORMATS = ("mp4", "gif", "webm")


def digest_format(format, caller=None):  # noqa: A002 — the public argument is named `format`
    from argdigest.core.caller import caller_matches

    formats = (
        ("mp4", "webm", "pngs", "html")
        if caller_matches(caller, "molsysviewer.viewer.movie.export_async")
        else MOVIE_FORMATS
    )
    if format is None:
        return None
    if isinstance(format, str) and format.strip().lower() in formats:
        return format.strip().lower()
    raise ArgumentError(
        "format",
        value=format,
        caller=caller,
        message=f"expected one of {', '.join(formats)}",
    )
