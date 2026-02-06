from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class NotSupportedSyntaxError(Exception):
    def __init__(self, syntax, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = f"The syntax {syntax} used in {caller} is not supported by MolSysViewer."
        if message:
            default_message += message

        full_message = message_from_catalog(
            "not_supported_syntax",
            extra={"syntax": syntax, "caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
