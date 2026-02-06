from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class NotWithThisFormError(Exception):
    """Exception raised when a method or a class cannot accept a specific form."""

    def __init__(self, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = ""
        if message:
            default_message += message

        full_message = message_from_catalog(
            "not_with_this_form",
            extra={"caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
