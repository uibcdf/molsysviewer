---
summary: 219 quarantined digesters are outside the package and undecided; deleting them is the open question.
issue: uibcdf/molsysviewer#78
status: open
opened: 2026-09-04
closed:
verification: measured
area: [argdigest, process]
guard:
normative:
blocked_by: []
supersedes: []
---

# 219 digesters that cannot run, and have not been deleted

**Opened:** 2026-09-04, because they had no entry anywhere. They were recorded in
`uibcdf/molsysviewer#70`'s comments and in `devtools/quarantine/README.md`, and neither is
a queue a decision surfaces from.

## What they are

`molsysviewer/_private/argdigest/argument/` was seeded by copying MolSysMT's directory
wholesale. ArgDigest resolves a digester by **argument name at call time**, so one whose
name no argument can carry is inert: imported at load, never consulted.

| batch | count | why they became unreachable |
| --- | ---: | --- |
| first (`#70`) | 120 | never reachable — copies of names this package's API does not use |
| second (`#75` phase C) | 99 | *made* unreachable by delegating the `get` family's digestion to MolSysMT |
| **total** | **219** | 362 remain |

They sit in `devtools/`, which `pyproject.toml` does not ship, so nothing loads, resolves or
distributes them.

## How each batch was verified

Six tests, and a name moved only if it failed all of them: not a public argument by the
inventory's own reachability walk; not a MolSysMT attribute or alias; refused by `msm.get`
when probed directly (**0 of 120 accepted**); never consulted across a recorded full-suite
run *attributed by config source*, so MolSysMT's own lookups are not miscounted as ours;
referenced by no surviving digester; mentioned nowhere in sources, tests or docs.

Then the check that mattered. `STRICTNESS` is `"warn"`, so a bad removal would be silent. It
was made loud: with `STRICTNESS = "error"` a missing digester raises, and the full suite was
run that way after each batch. **Zero `No digester for` both times.**

## Why this is not closed already

The six tests are heuristics stacked to be conservative, not a proof — and this same set has
been mis-measured twice. The first estimate said 273 files, from a method that missed the
`**kwargs` surface entirely; the spot-check that "confirmed" it re-ran the same flawed test.
`alternate_location` was offered as confirmed-dead and is a MolSysMT attribute. Both
corrections are dated in `#70`.

What survived those corrections is what is above. But the history is the reason for the
recommendation rather than a bare deletion.

## Recommendation

**Delete after the manual smoke test passes** — `devguide/smoke_test.md` drives flows the
automated suite does not, and has not been run since the second batch moved. If any of these
219 is reachable only from a human-driven path, that is where it appears.

`git mv` restores any of them; `devtools/quarantine/README.md` carries the per-batch
evidence and the command.
