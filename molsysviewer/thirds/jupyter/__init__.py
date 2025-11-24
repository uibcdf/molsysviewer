"""Jupyter helper for embedding pre-rendered MolSysViewer HTML in docs/notebooks."""

from pathlib import Path
from IPython.display import IFrame


def load_html_in_jupyter_notebook(filename: str | Path, *, width: str = "100%", height: str = "360px"):
    """Return an IFrame pointing to a pre-generated MolSysViewer HTML asset."""
    return IFrame(src=str(filename), width=width, height=height)


__all__ = ["load_html_in_jupyter_notebook"]
