"""A catalog warning must survive being rebuilt, because Python rebuilds it constantly.

SMonitor 0.13.0 fixed a defect whose whole danger is that it is silent. Python reconstructs
an exception or warning as ``type(w)(*w.args)`` -- ``pickle``, ``copy.deepcopy``,
``warnings.warn(text, category)`` and pytest-xdist between a worker and the controller all
do it. A class that names a domain field *first* receives its own rendered sentence as that
field and renders the template around it a second time. The message doubles.

Nothing about that fails loudly. The class imports, constructs, raises and is caught
normally; it only stops being itself after a round trip, in a doubled sentence somebody
eventually reads. `uibcdf/molsysviewer#63` asked for this guard for that reason, and
`uibcdf/molsysmt#161` is the same guard on their side.

The rule being held is SMONITOR_GUIDE §3.3.1: ``message`` first, domain fields keyword-only.
This file does not check the *shape* -- a signature can satisfy the letter and still double
-- it checks the property the shape exists to produce.
"""

from __future__ import annotations

import copy
import inspect
import pathlib
import pickle
import re
import subprocess
import warnings

import pytest

from molsysviewer._private.smonitor import CATALOG
import molsysviewer._private.smonitor.warnings as warnings_module

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: `from x import Y`, `import Y`, and the continuation lines of a parenthesised import.
_IMPORT_LINE = re.compile(r"\s*(from\s+\S+\s+import\b|import\b|[A-Za-z_][A-Za-z0-9_]*,\s*$)")

BASE = warnings_module.MolSysViewerCatalogWarning

#: Classes whose `catalog_entry` is absent from `CATALOG`, so constructing them raises
#: `KeyError`.
#:
#: **Empty, and meant to stay that way.** It held six entries for the length of one
#: session: `uibcdf/molsysviewer#73` found that commit a795953a added the classes and
#: neither the catalog entries nor the call-site migrations its own message described.
#: Finishing that work emptied this list.
#:
#: Nothing may be added here to silence a failure. A new broken class is a bug, and the
#: rot checks below exist so an entry cannot outlive its reason.
BROKEN_CATALOG_CLASSES = frozenset()

MESSAGE = "a concrete rendered sentence, with no template left in it"


def _catalog_classes() -> list[type]:
    found = [
        cls
        for _, cls in inspect.getmembers(warnings_module, inspect.isclass)
        if issubclass(cls, BASE) and cls is not BASE
    ]
    assert found, "no catalog warning classes found — has the module moved?"
    return sorted(found, key=lambda cls: cls.__name__)


def _healthy_classes() -> list[type]:
    return [c for c in _catalog_classes() if c.__name__ not in BROKEN_CATALOG_CLASSES]


@pytest.mark.parametrize("cls", _healthy_classes(), ids=lambda c: c.__name__)
def test_rebuilding_a_catalog_warning_does_not_change_its_message(cls):
    """The four ways Python rebuilds one, each of which the 0.13.0 defect broke."""
    original = cls(MESSAGE)
    rendered = str(original)

    # The property §3.3.1 exists to produce, checked before the round trips: a class whose
    # first positional is a domain field swallows the message into that field and renders
    # the template instead, so the sentence handed in never comes back out.
    assert rendered == MESSAGE, (
        f"{cls.__name__} did not keep the message it was given — its first positional "
        f"parameter is not `message`. Got: {rendered!r}"
    )

    assert str(type(original)(*original.args)) == rendered, "type(w)(*w.args) changed it"
    assert str(copy.deepcopy(original)) == rendered, "deepcopy changed it"
    assert str(pickle.loads(pickle.dumps(original))) == rendered, "pickle changed it"

    # How pytest-xdist moves a warning from a worker to the controller, and how a user's
    # own `warnings.warn(str(w), type(w))` re-raises one.
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        warnings.warn(rendered, cls)
    assert str(recorded[0].message) == rendered, "warn(text, category) changed it"


@pytest.mark.parametrize("cls", _healthy_classes(), ids=lambda c: c.__name__)
def test_a_catalog_warning_keeps_the_python_category_it_replaced(cls):
    """Migrating a call site must not drop the filters users already wrote.

    `CatalogWarning` derives from `Warning`, so a class that named only that base would
    silently escape every `filterwarnings("...", UserWarning)` in a user's code.
    """
    assert issubclass(cls, (UserWarning, RuntimeWarning, DeprecationWarning)), (
        f"{cls.__name__} names no original Python category, so user filters lose it"
    )


@pytest.mark.parametrize("cls", _catalog_classes(), ids=lambda c: c.__name__)
def test_every_catalog_class_names_an_entry_that_exists(cls):
    """`__init__` does `CATALOG[self.catalog_entry]`, so a wrong name is a KeyError.

    Not caught by anything else: an unused class never constructs, so it never raises.
    """
    if cls.__name__ in BROKEN_CATALOG_CLASSES:
        pytest.xfail(f"{cls.__name__} — uibcdf/molsysviewer#73")
    assert cls.catalog_entry in CATALOG, (
        f"{cls.__name__} names catalog entry {cls.catalog_entry!r}, which does not exist"
    )


def test_the_broken_list_does_not_rot():
    """A class that starts working must leave the list, or the list stops meaning anything."""
    repaired = sorted(
        cls.__name__
        for cls in _catalog_classes()
        if cls.__name__ in BROKEN_CATALOG_CLASSES and cls.catalog_entry in CATALOG
    )
    assert repaired == [], (
        f"these have catalog entries now — remove them from BROKEN_CATALOG_CLASSES "
        f"and let the real assertions cover them: {repaired}"
    )


def test_the_broken_list_names_classes_that_exist():
    """A renamed or deleted class must not leave a stale exemption behind."""
    known = {cls.__name__ for cls in _catalog_classes()}
    stale = sorted(BROKEN_CATALOG_CLASSES - known)
    assert stale == [], f"BROKEN_CATALOG_CLASSES names classes that no longer exist: {stale}"


@pytest.mark.parametrize("cls", _catalog_classes(), ids=lambda c: c.__name__)
def test_every_catalog_class_is_actually_raised_somewhere(cls):
    """A class nobody raises is a migration that was announced and not done.

    Commit a795953a said it routed nine warnings through the catalog. It added the classes
    and nothing else — no catalog entries, no call sites — and six of them sat unused and
    unconstructible until `uibcdf/molsysviewer#73`. Nothing failed, because an unused class
    never runs.

    Existence is not the property worth guarding; use is. The search excludes the module
    that defines them, so declaring a class is not evidence of raising it.
    """
    mentions = subprocess.run(
        ["grep", "-rn", cls.__name__, "molsysviewer/", "--include=*.py",
         "--exclude-dir=smonitor"],
        capture_output=True, text=True, cwd=ROOT,
    ).stdout.splitlines()

    # An import is not a use. Counting it would let a call site be reverted to a plain
    # `warnings.warn` while its now-unused import kept this test green — measured: it did.
    uses = [
        line for line in mentions
        if not _IMPORT_LINE.match(line.split(":", 2)[-1])
    ]

    assert uses, (
        f"{cls.__name__} is imported or declared but never raised. Either migrate the "
        f"call site it was written for, or delete the class — an unused catalog warning "
        f"reaches no user and no diagnostic."
    )
