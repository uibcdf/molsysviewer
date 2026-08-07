from molsysviewer._private.functions import caller_name
from smonitor.integrations import CatalogException
from molsysviewer._private.smonitor import CATALOG, META

class ArgumentError(CatalogException, ValueError):
    """Exception raised when a method, or a class, was not properly called or instantiated."""

    catalog_key = "argument_error"

    def __init__(self, argument, value=None, caller=None, message=None, **kwargs):
        if not caller:
            caller = caller_name()

        extra = {
            "argument": argument,
            "value": value,
            "caller": caller,
            "detail": message,
        }
        extra.update(kwargs)

        super().__init__(catalog=CATALOG, meta=META, extra=extra)
