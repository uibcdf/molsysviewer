"""Expose checkout-owned fixtures without changing scientific package discovery.

Installed-artifact CLIs load this helper by filename with ``runpy.run_path``.
Only the development-tool namespace is bound; ``sys.path`` remains untouched.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def expose_fixture_namespace(source_root):
    """Bind ``devtools`` to one selected checkout; reject competing fixtures."""
    directory = Path(source_root).resolve() / "devtools"
    if not (directory / "interaction_family_fixtures.py").is_file():
        raise ValueError(f"Scientific fixtures are missing from {directory}.")
    existing = sys.modules.get("devtools")
    if existing is not None:
        paths = {Path(path).resolve() for path in getattr(existing, "__path__", ())}
        if paths != {directory}:
            raise ValueError(f"The devtools namespace belongs to {paths}, expected {directory}.")
        return existing
    namespace = ModuleType("devtools")
    namespace.__path__ = [str(directory)]
    namespace.__spec__ = importlib.util.spec_from_loader("devtools", loader=None, is_package=True)
    sys.modules["devtools"] = namespace
    return namespace
