from __future__ import annotations

import os
from pathlib import Path

from smonitor import signal

from .._private.argdigest import digest


class IframeMarkup(str):
    """The ``<iframe>`` markup, which also renders where a renderer exists.

    One call serves both ways of embedding a view, because they are the same
    intent seen from two places:

    - in a notebook, evaluating it **shows the view**, like any other rich
      output;
    - anywhere else it is an ordinary string — print it, paste it into a
      Markdown or reStructuredText page, write it to a file, format it into a
      template.

    Returning plain text would have forced ``print()`` on the notebook path;
    returning only a display object would have made the paste-into-a-page path
    awkward. It is a ``str`` subclass, so nothing that works on strings stops
    working.
    """

    def _repr_html_(self) -> str:
        return str(self)


@signal(tags=["tools", "embed", "export"])
@digest()
def embed_iframe(
    filename: str,
    *,
    path: str,
    height: str = "480px",
    width: str = "100%",
    skip_digestion: bool = False,
) -> IframeMarkup:
    """Return the ``<iframe>`` markup that embeds an exported view in a page.

    ``filename`` is the exported HTML view, ``path`` the page that will embed it.
    Neither has to be absolute, and neither has to exist yet. The only rule is
    that **both are named from the same place** — typically the project root,
    which is how you named the view when you exported it. What is returned is
    the path from one to the other, and a shared starting point cancels out of
    that subtraction, so where you happen to be standing when you call this does
    not change the answer.

    That computation is the reason this exists. Counting directories by hand
    (``../../../_static/views/…``) is the one step of embedding that fails
    silently: the export succeeds, the build succeeds, and the reader gets an
    empty frame. Getting it wrong here is not possible.

    In a notebook, evaluating the call shows the view:

    ```python
    import molsysviewer as msv

    msv.tools.embed_iframe(
        "docs/_static/views/1tcd.html",
        path="docs/content/user/my_page.ipynb",
    )
    ```

    Everywhere else the same value is the markup itself, ready to paste into a
    Markdown or reStructuredText page. The path is resolved against the page's
    **directory**, which is also how the built site resolves it, so it works
    unchanged in Sphinx, MkDocs, Quarto or plain HTML.
    """
    view_path = Path(filename)
    page_dir = Path(path).parent
    src = Path(os.path.relpath(view_path.resolve(), start=page_dir.resolve())).as_posix()
    if not src.startswith((".", "/")):
        src = f"./{src}"
    return IframeMarkup(
        f'<iframe src="{src}" width="{width}" height="{height}"\n'
        f'        style="border:none;"></iframe>'
    )
