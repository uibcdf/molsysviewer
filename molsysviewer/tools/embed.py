from __future__ import annotations

import os
from pathlib import Path

from smonitor import signal

from .._private.arg_digestion import digest


@signal(tags=["tools", "embed", "export"])
@digest()
def embed_iframe(
    filename: str,
    *,
    path: str,
    height: str = "480px",
    width: str = "100%",
    skip_digestion: bool = False,
) -> str:
    """Return the ``<iframe>`` markup that embeds an exported view in a page.

    ``filename`` is the exported HTML view, ``path`` the page that will embed it.
    Both are given as you know them — from the project root, or relative to where
    you are standing — and the relative ``src`` between them is computed here.

    That computation is the reason this exists. Counting directories by hand
    (``../../../_static/views/…``) is the one step of embedding that fails
    silently: the export succeeds, the build succeeds, and the reader gets an
    empty frame. Getting it wrong here is not possible.

    ```python
    import molsysviewer as msv

    print(msv.tools.embed_iframe(
        "docs/_static/views/1tcd.html",
        path="docs/content/user/my_page.md",
    ))
    ```

    The path is resolved against the page's **directory**, which is also how the
    built site resolves it, so the markup can be pasted into Sphinx, MkDocs,
    Quarto or plain HTML unchanged.
    """
    view_path = Path(filename)
    page_dir = Path(path).parent
    src = Path(os.path.relpath(view_path.resolve(), start=page_dir.resolve())).as_posix()
    if not src.startswith((".", "/")):
        src = f"./{src}"
    return (
        f'<iframe src="{src}" width="{width}" height="{height}"\n'
        f'        style="border:none;"></iframe>'
    )
