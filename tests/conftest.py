from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Ensure `pytest` and `python -m pytest` resolve the in-repo package the same way.
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)


def _close_registered_molsysviewer_widgets() -> None:
    from ipywidgets.widgets.widget import _instances

    from molsysviewer.addons import AddonPanelWidget
    from molsysviewer.widget import MolSysViewerWidget

    for widget in list(_instances.values()):
        if not isinstance(widget, (MolSysViewerWidget, AddonPanelWidget)):
            continue
        view_ref = getattr(widget, "_molsysviewer_view_ref", None)
        view = view_ref() if callable(view_ref) else None
        if view is not None:
            view.close()
            continue
        layout = getattr(widget, "layout", None)
        widget.close()
        if layout is not widget:
            close_layout = getattr(layout, "close", None)
            if callable(close_layout):
                close_layout()


@pytest.fixture(autouse=True)
def _close_molsysviewer_widgets_after_each_test():
    """Keep open AnyWidgets from retaining complete views between tests."""
    yield

    _close_registered_molsysviewer_widgets()
