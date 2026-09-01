"""MolSysViewer warnings backed by the SMonitor catalog.

A warning raised with `warnings.warn(text)` reaches SMonitor only through the
`py.warnings` logger, if `capture_warnings` is on at all: with `code=None`,
`source="py.warnings"`, no category and none of its structured fields. Nothing keyed on
codes can see it -- not `events_by_code`, not a fingerprint summary, not a QA policy.
A catalog warning raised through `warn()` arrives coded and structured, and still reaches
`pytest.warns`, `filterwarnings` and `simplefilter("error")` exactly as before.

**Deprecations are deliberately not here.** `tests/test_documentation_pages_run.py`
derives what the library deprecates by reading the *literal* first argument of every
`warnings.warn(..., DeprecationWarning)` in the package, and refuses to run when it finds
none. Moving those twenty call sites onto a catalog class would leave that derivation
with nothing to read, and the documentation guard it feeds -- the one that stops a page
teaching a deprecated call -- would stop covering without failing. MolSysMT reached the
same conclusion and says so in its own `MolSysMTDeprecationWarning`.
"""

from __future__ import annotations

from smonitor.integrations import CatalogWarning

from . import CATALOG, META
from .emitter import bundle

warn = bundle.warn
warn_once = bundle.warn_once


class MolSysViewerCatalogWarning(CatalogWarning):
    # Subclasses below name their original Python category as a second base. A
    # `CatalogWarning` derives from `Warning`, so migrating a call site without it would
    # silently drop every `filterwarnings("...", UserWarning)` and
    # `simplefilter("error", RuntimeWarning)` a user already has. The migration adds a
    # code and structured fields; it must take nothing away.
    """Base for this library's catalog warnings.

    `message` comes first and the domain fields are keyword-only, so that
    `type(w)(*w.args)` -- how `pickle`, `copy.deepcopy`, pytest-xdist and
    `warnings.warn(text, category)` all rebuild a warning -- hands the rendered text back
    as the message rather than as a field. Keyword-only keeps a misspelled field an error
    instead of a silently ignored one. The mould is MolSysMT's, and the reason it has
    that shape is smonitor 0.13.0's `args`-idempotence fix.

    The code is passed explicitly rather than resolved from `catalog_key`: this package's
    catalog is flat, and while SMonitor falls back to a flat lookup, naming the code here
    means a renamed catalog key fails at import instead of silently resolving to nothing.
    """

    catalog_entry: str | None = None

    def __init__(self, message=None, **kwargs):
        entry = CATALOG[self.catalog_entry] if self.catalog_entry else None
        super().__init__(
            message,
            code=entry["code"] if entry else None,
            catalog=CATALOG,
            meta=META,
            **kwargs,
        )


class StructureScaleWarning(MolSysViewerCatalogWarning, UserWarning):
    """A load whose materialized coordinates exceed the configured budget.

    The name is the one this warning has always had; what changed is that it is now
    backed by the catalog. Callers filtering or asserting on it are unaffected.
    """

    catalog_entry = "structure_scale_over_budget"

