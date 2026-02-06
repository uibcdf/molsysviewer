from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class NotImplementedIteratorError(Exception):
    def __init__(self, form, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = f"Iterator has not been implemented for form {form}"
        if message:
            default_message += message

        full_message = message_from_catalog(
            "not_implemented_iterator",
            extra={"form": form, "caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
