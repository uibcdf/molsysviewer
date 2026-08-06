# Executing the documentation in CI

**Status:** **done 2026-08-06** — `.github/workflows/docs-notebooks.yaml`. Kept
for the reasoning, and for one correction it needed before it could work.

## What happened

In July 2026, ten documented notebooks were broken and nothing reported it. They
had been broken since an earlier round hardened the argument digesters
(`84ede163`), which is exactly the kind of change that breaks examples.

Four independent causes, found by running them:

- digesters rejecting `molsysviewer.viewer.get` as a caller, which broke 58 of
  the 81 query arguments and therefore most `view.get(...)` examples;
- bare numbers where the API now requires explicit units;
- cells that cannot run without a browser (camera snapshot, movie camera orbit);
- errors in the documentation itself: an undefined alias, a `sidechain`
  selection MolSysMT does not have, and five values for a seven-group system.

## Why nothing caught it

`docs/conf.py` sets `nb_execution_mode = "off"`, so Sphinx renders the stored
outputs without running anything. **A green `make html` proves nothing about
whether the documented code still works.** The real check is
`docs/execute_notebooks.py`, and no workflow runs it.

This is the same shape as two other defects found in the same round: the
boundary audit asked whether a digester existed but never whether it accepted
the viewer as caller, and Qt classified its transport events from a hardcoded
literal nothing tied to the shared manifest. **Where two things must agree and
nothing mechanically forces them to, they drift in silence.** Documentation and
the API are two such things.

## Proposal

Run `docs/execute_notebooks.py` in CI. Points worth deciding before wiring it:

- **Cost.** The 52 notebooks take a few minutes and load real molecular systems.
  A separate workflow, or a path filter on `docs/**` plus the public API, keeps
  it off the critical path.
- **Headless honesty.** Some cells genuinely need a browser. The current fix
  guards them and *explains why* rather than silencing them, which is the
  pattern to keep: a skipped cell must say what it would have needed.
- **Blocking or not.** Blocking is defensible — a broken example is a broken
  public contract — but a flaky notebook must never gate an unrelated fix.
  Starting non-blocking and promoting it once it proves stable is the safer
  order.
- **Where the outputs go.** The runner writes `.nbconvert.log` and
  `.last_run` files next to each notebook; CI should not commit those back.

## Acceptance

- A workflow executes the documentation and fails visibly when a notebook does.
- A change that breaks a documented example is reported by CI, not by a user.


---

## How it was wired, 2026-08-06

**The trigger is a change in the library, not in the notebooks**, and that
correction is the whole design. This file records that the ten broke when the
argument digesters were hardened — *their own sources were untouched*. Any
incremental mechanism skips an unchanged notebook by definition, so a gate driven
by this project's run marks would have skipped all ten and reported green. The
workflow therefore runs with `--force` and consults no mark.

Path-filtered to `molsysviewer/**` and `docs/**`, plus a weekly schedule so a
break arriving from a dependency is found by a job rather than by a reader.
Blocking, which the "points worth deciding" above left open: measured at **44
seconds for all 23 notebooks** with four workers, on a suite that is green today,
so it does not gate unrelated work by being slow.

**Three preconditions had to be fixed first**, and none of them were in this file:

- the script **always exited 0**. A gate on it would have reported success while
  examples were broken — the same defect this proposal describes, one level up;
- it printed the path of a log rather than the failure, so a red build told you
  nothing without downloading artifacts. It now prints the failing cell and the
  exception, and the workflow uploads the logs anyway;
- its main loop swallowed exceptions raised outside a notebook, so an
  infrastructure failure was indistinguishable from a broken example.

The run marks stay, with their meaning corrected: they answer *"did I change
it?"* for local and bulk runs, never *"does it still work?"*. See the commit that
made them content-based.

**Not adopted: `pytest --nbmake`.** It would give `--lf` and marker integration,
but it does not write outputs back, so it cannot replace the script that produces
the committed notebooks — it would leave two executors for one corpus, which is
the shape of drift this repository has spent a week removing. Reconsider only if
the reporting proves inadequate in practice.
