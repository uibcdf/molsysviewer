from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class LibraryNotFoundError(Exception):
    """Exception raised when a library required by the user is not found."""

    def __init__(self, library, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = f"The python library {library} was not found. "
        if message:
            default_message += message

        full_message = message_from_catalog(
            "library_not_found",
            extra={"library": library, "caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
