---
summary: What the 264 unused-import reports actually were, why only 60 were real, and how the one wrong removal silenced every diagnostic in the package.
issue:
status: closed
opened: 2026-09-04
closed: 2026-09-04
verification: measured
area: [tooling, process]
guard: tests/test_catalog_templates_render.py
normative:
blocked_by: []
supersedes: []
---

# 264 unused imports, 60 of them real

**Measured:** 2026-09-04. `ruff --select F401` reported 264 across `molsysviewer/`, `tests/`
and `devtools/`. The number is not the size of the problem, and the difference is worth
recording because the obvious action — `ruff --fix` — would have been wrong four ways.

## The four populations

| population | count | treatment |
| --- | ---: | --- |
| `devtools/quarantine/` | 83 | **untouched** — awaiting deletion in `uibcdf/molsysviewer#78` |
| `_private/argdigest/argument/` | 61 | **untouched** — copies of MolSysMT's, and the same imports are unused *there* |
| `__init__.py` re-exports | 59 | **untouched** — deleting them breaks 30 imports |
| everything else | 61 | 60 cleaned, 1 restored (see below) |

**Quarantine.** Cleaning files whose next commit deletes them is work that cannot pay off,
and it would make them diverge from the MolSysMT originals anyone comparing them would use.

**The digester copies.** Same argument, and sharper: `uibcdf/molsysviewer#70` is about two
copies drifting. `import numpy as np` is unused in *their* `n_peptides.py` too. Removing it
here buys a clean lint line and costs the ability to `diff` the two directories.

**The `__init__.py` files.** `_private/exceptions/__init__.py` re-exports fourteen exception
classes with no `__all__`, so ruff calls every one unused; `from ._private.exceptions import
ArgumentError` appears in thirty places. These are the public surface of their packages,
written in the style the codebase already uses.

## The one that would have broken at runtime

`standalone_qt/application.py` and `standalone_qt/menus.py` account for 28 of the reports,
and **every one of them is load-bearing**:

```python
def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]          # <- the imports exist for this line
```

The helpers are resolved **by string**. Ruff cannot see a `globals()[name]` lookup, so it
reports each import as unused; deleting them raises `KeyError` at runtime, in the Qt host,
which no unit test would attribute to a missing import. They now carry `# noqa: F401` and
the reason.

This is the second time this shape has cost something here: `viewer/camera.py` once lost
`import molsysmt as msm` to `ruff --fix`, breaking a test's patch target, and carried a
comment saying so until phase D gave the import a second, visible use.

## How the 61 were checked

Each candidate was resolved against the whole tree before deletion — is the name referenced
as `<module>.<name>` anywhere, is it in an `__all__`, does it appear in a string. One
survived that filter and was still wrong: `re` in `viewer/load.py` looked used because
`load.re` matched `load.reset` and 77 similar. It was confirmed unused by asking for
`re.<something>` instead, and removed.

Every edit was parsed with `ast` before being written, which is what stopped the two Qt
files being corrupted: the script refused to write them and said so.

## The one that did break — caught by the suite, not by the check

The check above has a hole, and `_smonitor.py` fell through it. Its last line was:

```python
from molsysviewer._private.smonitor.catalog import CODES, SIGNALS
```

`_smonitor.py` is a **configuration module**: SMonitor reads `CODES` and `SIGNALS` off it by
attribute, the same way ArgDigest reads `DIGESTION_SOURCE`. The names are the module's
contract with an external framework, not local variables — so they are never referenced as
`_smonitor.CODES` anywhere in this tree, and every question the check asks about them
answers "unused".

Removing the line did not raise. Every catalog message rendered as the **empty string**:
`SceneHistoryOverBudgetWarning('')`. The diagnostics kept their class and lost their text.
15 tests failed, all of them assertions on message content — a diagnostic that still fires
with the right type and says nothing is exactly the failure that survives a suite asserting
only on `pytest.warns(SomeWarning)`.

Restored with `# noqa: F401` and the reason.

The Qt case was caught and this one was not, and the difference says what to look for: in
`application.py` the consumer — `globals()[name]` — sits in the same file, so reading the
file reveals it. Here the consumer lives in another package. **The rule this yields: an
import in a module some framework reads by attribute is a contract, and the only way to see
it is to know the module is config.** This repo has two such modules, `_argdigest.py` and
`_smonitor.py`; `_argdigest.py` was untouched.

## Result

61 imports removed across 26 files, 29 marked as load-bearing (28 in Qt, 1 in `_smonitor.py`
after the suite caught it), the other 203 reports left standing with a reason each.

Of 264 reports, **60 were real** — 23%. `ruff --fix` would have been wrong four ways over
the other 77%, and one of those ways renders every diagnostic in the package silent.
