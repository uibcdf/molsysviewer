from ..functions import caller_name
from ..smonitor_emit import message_from_catalog


class MolecularSystemsNeededError(Exception):
    def __init__(self, caller=None, message=None):
        if not caller:
            caller = caller_name()

        default_message = (
            f"The function or method {caller} works over multiple molecular systems. "
            f"Either no molecular system or a single system was provided."
        )
        if message:
            default_message += message

        full_message = message_from_catalog(
            "molecular_systems_needed",
            extra={"caller": caller, "detail": message},
            default_message=default_message,
        )

        super().__init__(full_message)
