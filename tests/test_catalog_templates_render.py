"""Every catalog template must actually render.

`_smonitor.py` is a configuration module: SMonitor reads `CODES` and `SIGNALS` off it by
attribute, so the import that puts them there looks unused to every static check and to
every question one can ask about this tree -- the names are never referenced as
`_smonitor.CODES` anywhere, because their consumer lives in another package. On 2026-09-04
that import was deleted as dead, and the package's whole diagnostic vocabulary went silent:
each warning kept its class and rendered as the empty string,
`SceneHistoryOverBudgetWarning('')`.

Fifteen tests caught it, all of them assertions on message *content*. Anything asserting
only `pytest.warns(SomeWarning)` passed, which is the same shape as the older defect
recorded above `MESSAGES` in `catalog.py`: for months no template rendered at all and
nothing looked broken, because every caller passed a `default_message` that hid it.

This module closes both. It renders from `MESSAGES` -- authored data, independent of
whether SMonitor's registration worked -- and passes no `default_message`, so a broken
registration has nothing to fall back to. Deriving the expected set by rendering instead
would be circular: if rendering breaks everywhere, the set empties and the test passes
while asserting nothing.
"""

from string import Formatter

import pytest

from molsysviewer._private.smonitor.catalog import CATALOG, MESSAGES
from molsysviewer._private.smonitor_emit import message_from_catalog

KEYS = sorted(set(MESSAGES) & set(CATALOG))


def _placeholders(template):
    return [f for _, f, _, _ in Formatter().parse(template) if f]


def _literals(template):
    """The text a template owns outright, with the substituted parts taken out."""
    return [text.strip() for text, _, _, _ in Formatter().parse(template) if text.strip()]


def test_catalog_and_messages_are_not_empty():
    # Guards the guard: were MESSAGES or CATALOG ever emptied, every parametrised case
    # below would silently vanish and this file would assert nothing.
    assert len(KEYS) >= 30, f"expected the full catalog, got {len(KEYS)} keys"


@pytest.mark.parametrize("key", KEYS)
def test_template_renders_its_own_words(key):
    template = MESSAGES[key]
    extra = {name: f"<{name}>" for name in _placeholders(template)}
    rendered = message_from_catalog(key, extra=extra)

    assert rendered, (
        f"catalog entry {key!r} rendered as the empty string. Its diagnostic will fire "
        f"with the right class and no text. Check that molsysviewer/_smonitor.py still "
        f"imports CODES and SIGNALS -- SMonitor reads them off that module by attribute."
    )
    for literal in _literals(template):
        assert literal in rendered, (
            f"catalog entry {key!r} lost authored text {literal!r} from its template"
        )


@pytest.mark.parametrize("key", KEYS)
def test_template_substitutes_every_placeholder(key):
    template = MESSAGES[key]
    names = _placeholders(template)
    if not names:
        pytest.skip("template has no placeholders")
    extra = {name: f"<{name}>" for name in names}
    rendered = message_from_catalog(key, extra=extra)
    for name in names:
        assert f"<{name}>" in rendered, (
            f"catalog entry {key!r} did not substitute {{{name}}}; the detail the caller "
            f"passed in `extra` never reached the user"
        )
