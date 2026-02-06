from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class IteratorError(Exception):
    def __init__(self, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = "An error was found in the iterator arguments. "
        if message:
            default_message += message

        full_message = message_from_catalog(
            "iterator_error",
            extra={"caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
