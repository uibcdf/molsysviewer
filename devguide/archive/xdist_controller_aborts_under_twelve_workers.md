---
summary: With pytest -n 12 the xdist controller aborts mid-run and reports a partial result.
issue: uibcdf/molsysviewer#76
status: resolved
opened: 2026-09-04
closed: 2026-09-04
severity: low
verification: measured
area: [testing, tooling]
guard: tests/conftest.py (the controller-side imports; removing them restores the abort)
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


## Second pass — 2026-09-04 — the mechanism, the precondition, and the link still missing

### `Widget.__del__` can raise, and now it is known how

`Widget.__del__` calls `close()`, which calls `comm.close()`, which ends in
`CommManager.unregister_comm`:

```python
def unregister_comm(self, comm):
    # unlike get_comm, this should raise a KeyError
    comm = self.comms.pop(comm.comm_id)
```

A comm the manager no longer holds therefore raises `KeyError` inside a destructor, which
Python reports as an ignored exception and pytest turns into
`PytestUnraisableExceptionWarning`. Reproduced deliberately with a bare `ipywidgets.Widget`.

### It does not happen in this suite, measured three ways

Instrumented across a full run:

| probe | result |
| --- | ---: |
| widgets still registered at session end (5 processes) | **0** |
| `unregister_comm` raising `KeyError` | **0** |
| unraisable exceptions after a forced `gc.collect()` per test | **0** |

So the widget hygiene is clean *when the suite is green* — which is the condition both
crashing runs did not meet.

### The precondition, which is ours and is now fixed

Both crashes happened during `uibcdf/molsysviewer#75` phase C, in a window where
`view.close()`'s neighbourhood raised `AttributeError` because a method had been removed
while a caller still used it. The teardown fixture was a bare loop:

```python
for widget in list(_instances.values()):
    ...
    view.close()
```

**One refusing widget ends the loop and leaves every widget after it registered for the
rest of the session.** Measured: a single failing `close()` stranded all four widgets alive
at that moment. Stranded widgets are exactly the ones that can later be finalised holding a
live comm — the state the mechanism above needs.

The loop now closes every widget regardless, unregisters and closes the comm of any that
refuses, and reports the failure to stderr instead of swallowing it. Guarded by
`tests/test_teardown_leaves_no_widget_registered.py`, mutation-verified by restoring the
bare loop.

### What is still not established

That this *is* the crash. Eight further runs at `-n 12` did not reproduce it, all green.
The chain — stranded widget → late finalisation → unraisable → xdist shipping the warning →
controller abort — is plausible at every link and demonstrated at the first and the second.
The third and fourth are not.

**Left `partial` rather than closed.** The precondition is removed and the suite is clean;
whether that is sufficient will be known only by the crash not recurring, which is not
evidence anybody can produce on demand.


## Third pass — 2026-09-04 — resolved: the trigger, and it was never the warning class

The missing link was found by running plain `pytest`, without `--receptor=llm`. The receptor
report compresses worker output; the raw run prints the controller's traceback in full, and
it names every step.

### The chain, end to end

1. A worker emits a warning whose class lives in a `molsysmt.*` module.
2. xdist sends the class's **module name** to the controller.
3. Under `-n 12` the controller schedules but never collects, so it has never imported
   `molsysmt`. `unserialize_warning_message` therefore calls `importlib.import_module` on
   it **from the receiver thread** — a full, cold `import molsysmt`.
4. That import reaches `molsysmt/_pyunitwizard.py`, which calls
   `puw.configure.set_standard_units`.
5. PyUnitWizard's registry is not safe to build from two threads. The reader gets
   `KeyError: 'pint'` from `dict_translate_quantity['string']['pint']`.
6. `unserialize_warning_message` guards only `TypeError`. The `KeyError` kills the receiver
   thread; the node goes down mid-test.
7. Only then does the scheduler hit `KeyError: <WorkerController gw8>` — **the symptom this
   document was opened under, two steps removed from its cause.**

The first pass was right to reject the warning classes. The class was never the problem:
the problem is the *import* that looking the class up triggers.

### The race, isolated

It needs neither pytest nor xdist:

```python
barrier = threading.Barrier(2)
threading.Thread(target=lambda: (barrier.wait(), __import__("molsysmt"))).start()
threading.Thread(target=lambda: (barrier.wait(), __import__("molsysviewer"))).start()
```

Two different top-level packages mean two different import locks, so nothing serializes the
two clients that configure PyUnitWizard. Traced across both threads, the losing one calls
`_parse_with_pint('nm')` with `loaded_libraries` still empty: it never called
`load_library`, because it found `pyunitwizard` already in `sys.modules` — put there by the
other thread — and proceeded as though the package were configured.

| state | `KeyError: 'pint'` | smonitor `AttributeError` | clean |
| --- | ---: | ---: | ---: |
| as released | 24/25 | 1/25 | 0 |
| + PyUnitWizard fix | 0 | 24/25 | 1/25 |
| + smonitor fix | 0 | 0 | **25/25** |

Filed as [uibcdf/PyUnitWizard#70](https://github.com/uibcdf/pyunitwizard/issues/70) and
[uibcdf/smonitor#3](https://github.com/uibcdf/smonitor/issues/3), each with the patch that
produced the row above.

### A wrong turn worth recording

Three plain runs were clean while runs with `--receptor=llm` crashed, which looked like
evidence that our own pytest plugin was destabilising the session. It was not: plain
`pytest` went on to crash **2 of 4** with the identical `KeyError: 'pint'`. Stopping at the
first three would have filed a false report against `pytest-receptor`.

A second wrong turn: commit `882d30fa` ("declare the unit policy at import instead of on
first use") looked like the change that created a second concurrent configurator. Disabling
that import does not stop the race — `molsysviewer` imports `molsysmt` regardless — so the
commit is not the cause.

### The fix here

`tests/conftest.py` imports both packages at module scope. The controller loads conftest;
the workers load it too, harmlessly. With both already in `sys.modules`, xdist's
`import_module` is a dict lookup and no import runs in the receiver thread at all.

This is a local fix to a defect that lives in three other projects, and it is the right one
to hold: it costs one import in the controller and removes the whole class of failure from
this suite regardless of when the upstream fixes land.

**Measured:** 2 internal errors in 4 plain runs before; **0 in 8 runs after**. Under the
observed rate that is p ≈ 0.4%. The single failure among those 8 was
`test_qt_event_transport_smoke_real_qt`, an unrelated Qt subprocess flake with no
`INTERNALERROR` and no `KeyError`.

### What is still upstream's

xdist performs an arbitrary import in its receiver thread and lets any non-`TypeError`
exception from it end the session. Even with the two UIBCDF fixes, any package whose import
raises will take a run down and report it as a scheduler `KeyError`. That report is drafted
and awaiting a decision on filing it to `pytest-dev/pytest-xdist`.


## Correction — 2026-09-04 — pytest-receptor did not hide anything

The third pass above says the link was found "by running plain `pytest`, without
`--receptor=llm`", and that "the receptor report compresses worker output". **That is
wrong, and the correction matters because the sentence reads as a defect report against a
sibling tool.**

Both runs of the same failure were compared line for line:

| | `INTERNALERROR` lines | `KeyError: 'pint'` |
| --- | ---: | ---: |
| `--receptor=llm` | 93 | 1 |
| plain `pytest` | 93 | 1 |

Identical. The receptor passes the controller's traceback through untouched and prints its
own summary after it, on line 97 of the same output.

What actually happened is that every look at the receptor runs went through
`grep -E "^PASS|^FAIL|^ERROR"` or `tail`, and through `.pytest_cache/d/receptor/last-run.txt`
— all of which show the summary and not the 93 lines above it. The traceback was on screen
the whole time and was filtered out by the person reading it, not by the tool producing it.

Nothing is to be reported against `pytest-receptor`. The standing rule ("plain pytest only
when suspicious") was applied correctly; the conclusion drawn about *why* it helped was not.

The three clean plain runs recorded in "A wrong turn worth recording" stand as measured —
they were clean — but they were coincidence, not evidence about the reporter.
