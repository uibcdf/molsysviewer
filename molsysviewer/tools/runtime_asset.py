from __future__ import annotations

from pathlib import Path

from smonitor import signal

from .._private.arg_digestion import digest
from .._private.runtime_asset import place_runtime_asset


@signal(tags=["tools", "runtime", "export"])
@digest()
def export_runtime_asset(
    output_directory: str,
    *,
    skip_digestion: bool = False,
) -> Path:
    """Copy the bundled MolSysViewer runtime into ``output_directory``.

    Use this when a build system needs the runtime without constructing a scene —
    a documentation `Makefile` or CI step that places the asset once and then
    exports several views against it.

    ``view.export.html(..., mode="lite")`` already does this for you; this
    function exists for the case where the asset and the views are produced by
    different steps.

    The copy is idempotent by content: an asset already present at the installed
    version is left alone, and one from a different version is replaced. That is
    what keeps a runtime shared by several views coherent with all of them.

    Returns the path of the placed asset.
    """
    return place_runtime_asset(output_directory)
