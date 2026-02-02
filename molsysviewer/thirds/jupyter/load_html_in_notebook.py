"""Jupyter helper for embedding pre-rendered MolSysViewer HTML in docs/notebooks."""

from pathlib import Path
from IPython.display import IFrame

from ..._private.digestion import digest


@digest()
def load_html_in_notebook(
    filename: str | Path,
    *,
    width: str = "100%",
    height: str = "480px",
    skip_digestion: bool = False,
):
    """Return an IFrame pointing to a pre-generated MolSysViewer HTML asset.

    The default height matches the default canvas height used by the
    MolSysViewer widget layout.
    """
    return IFrame(src=str(filename), width=width, height=height)
