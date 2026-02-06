from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class ArgumentError(Exception):
    """Exception raised when a method, or a class, was not properly called or instantiated."""

    def __init__(self, argument, value=None, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = f"Error in {caller} due to the {argument} argument with value {value}."
        if message:
            default_message += message

        full_message = message_from_catalog(
            "argument_error",
            extra={
                "argument": argument,
                "value": value,
                "caller": caller,
                "detail": message,
            },
            default_message=default_message,
        )

        super().__init__(full_message)
