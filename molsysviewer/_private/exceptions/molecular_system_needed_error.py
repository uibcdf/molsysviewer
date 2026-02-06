from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class MolecularSystemNeededError(Exception):
    def __init__(self, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = (
            f"The function or method {caller} works over a molecular system. "
            f"Either no molecular system or multiple systems were provided."
        )
        if message:
            default_message += message

        full_message = message_from_catalog(
            "molecular_system_needed",
            extra={"caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
