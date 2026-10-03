from smonitor.integrations import CatalogException

from ..smonitor import CATALOG, META


class InteractionAnalysisError(CatalogException, ValueError):
    """A rejected scientific interaction operation, with catalog diagnostics."""

    def __init__(self, message=None, *, reason=None, extra=None):
        code = None if reason is None else CATALOG[f"interaction_{reason}"]["code"]
        super().__init__(message, code=code, extra=extra, catalog=CATALOG, meta=META)
