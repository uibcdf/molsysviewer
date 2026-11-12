"""Connector-owned Movie capture context; ordinary Python calls use primary."""

from contextvars import ContextVar

from .frontend_requests import FrontendRequestError
from .visual_capture import capture_endpoint

MOVIE_ENDPOINT = ContextVar("molsysviewer_movie_endpoint", default=None)
MOVIE_REVISION = ContextVar("molsysviewer_movie_revision", default=None)


def movie_endpoint(view):
    return capture_endpoint(view, MOVIE_ENDPOINT.get())


def check_movie_revision(movie):
    expected = MOVIE_REVISION.get()
    if expected is not None and expected != movie._studio_revision:
        raise FrontendRequestError(
            "The Movie changed. Refresh the editor before continuing.", reason="movie_seek_superseded"
        )
