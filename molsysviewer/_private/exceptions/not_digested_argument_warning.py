from ..smonitor_emit import message_from_catalog


class NotDigestedArgumentWarning(Warning):
    def __init__(self, argument, caller=None, message=None):
        default_message = f"The {argument} argument was not digested."
        if message:
            default_message += message

        full_message = message_from_catalog(
            "not_digested_argument",
            extra={"argument": argument, "caller": caller or "", "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
