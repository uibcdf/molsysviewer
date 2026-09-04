---
summary: With pytest -n 12 the xdist controller aborts mid-run and reports a partial result.
issue: uibcdf/molsysviewer#76
status: open
opened: 2026-09-04
closed:
severity: low
verification: observed
area: [testing, tooling]
guard:
normative:
blocked_by: []
supersedes: []
---

# A truncated run is not a smaller run

**Observed:** 2026-09-04, twice, while executing `uibcdf/molsysviewer#75`. Severity is low
because nothing about the library is wrong; it is here because of what it does to the one
instrument used to decide whether the library is wrong.

## What happens

```
ERROR exit=3 | 2 failed, 847 passed, 1 skipped | incomplete: 850 of 1804 executed | internal error
```

The controller aborts. Two internal errors appear together: `unserialize_warning_message`
failing inside `importlib.import_module`, and then `KeyError: <WorkerController gw10>` in
the scheduler once that worker is gone. Both runs also carried
`PytestUnraisableExceptionWarning: Exception ignored in: <function Widget.__del__>`.

## What it is not

Measured rather than assumed, because the shape of it points straight at
`uibcdf/molsysviewer#63` and that turned out to be a red herring:

| suspicion | result |
| --- | --- |
| our catalog warnings fail xdist's `cls(*args)` rebuild | **no** — all ten round-trip through xdist's own serializer |
| `PytestUnraisableExceptionWarning` fails it | **no** — round-trips; its module is `pytest` |
| importing our warnings module is expensive enough to matter | **no** — 0.35 s, 590 modules, and MolSysMT is not among them |
| views leak widgets that finalise late | **no** — `view.close()` empties `_instances` |
| test order shuffling | **no** — `pytest-randomly` is not installed |

## What is not known

The trigger. Four further attempts at `-n 12` did not reproduce it: two on a green suite,
two with a deliberately failing test. It appears to need the `Widget.__del__` unraisable,
which comes from a widget finalised at interpreter shutdown rather than through
`view.close()`, and that could not be forced.

**Recorded unfinished on purpose.** The alternative was to keep going until a story fitted,
and the measurements above are worth more to whoever picks this up than a guess would be.

## Why it is worth a record at all

`unserialize_warning_message` runs `importlib.import_module` in the controller's receiver
thread and guards only `TypeError`. Anything else ends the session, and the session takes
the results with it — the run above discarded the outcome of 954 tests.

## Exposure

**CI does not use `-n`.** `.github/workflows/CI.yaml` runs `pytest` single-process; the
`-n logical` line is commented out. This cannot reach CI.

Locally, `-n 4` has not reproduced it. And the receptor report already prints
`incomplete: N of M executed`, so a truncated run announces itself rather than passing for
a smaller one — which is the property that keeps this at low severity rather than high.
