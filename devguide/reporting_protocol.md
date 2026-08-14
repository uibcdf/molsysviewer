# Reporting protocol

How a defect or a proposal enters `pending_bugs/` and `pending_proposals/`, and how those
two directories stay in step with the GitHub issue board.

Adopted 2026-08-14 from
[MolSysMT's protocol](https://github.com/uibcdf/MolSysMT/blob/main/devguide/reporting_protocol.md),
which is the canonical version and covers more ground. This file records the part
MolSysViewer runs and the two places where we differ.

## The rule

**If it deserves a document in one of those two directories, it deserves an issue.**

We have never written a pending document for a typo or a rename, so the document is
already the significance filter and no second one is needed.

The two records have different jobs and must not be given the same one:

| | holds | changes |
| --- | --- | --- |
| the document | the analysis, the measurements, the refuted paths | continuously |
| the issue | state, and the settled facts a reader outside the repository needs | at two moments only |

**The issue is written when it opens and when it closes. It is not maintained in
between.** If the analysis changes on the way, the document is corrected; the issue is
not rewritten, and the closing comment states the final truth.

## Identity

The issue number is the stable identity. Filenames are local names and may change; issue
numbers may not.

Cross-repository references are `uibcdf/<repo>#<number>`, never a path into another
repository's `devguide/`. We learned this the expensive way: a report filed into
`../argdigest/devguide/pending_bugs/` was consumed by the fix and deleted, and the
reference to it broke silently. An issue number does not break; it closes.

## Front matter

Every document in the two queues begins with it:

```yaml
---
summary: One line, present tense. Feeds the issue title.
issue: uibcdf/molsysviewer#34
status: open
opened: 2026-08-08
closed:
severity: medium          # bugs only
verification: reproduced
area: [export, embedding]
guard:                    # the test that fails if it comes back
normative:                # or the document that absorbed the rules
blocked_by: []
supersedes: []
---
```

`status` — `open`, `active`, `blocked`, `partial` are the **open set**; `resolved`,
`withdrawn`, `superseded` are the **closed set**, and a document in the closed set belongs
under `archive/`.

`partial` earns its place here. Three of our entries were carrying that state in prose —
the Qt host at "fix in, confirmation pending", five of six findings acted on — where
nothing could query it.

`verification` — how solid the report's own diagnosis is: `reproduced`, `measured`,
`inspected`, `upstream`, `asserted`.

**`asserted` is permitted, and it is the field that would have caught our own mistake.**
A report claiming `add_pharmacophore_features` was broken by an upstream defect was
believed, not run; it turned out the function was never callable that way for an unrelated
reason. Labelled `asserted`, the debt would have been visible instead of reading as a
finding.

## Closing

An entry closes when three things exist: the change, the record, and something that fails
if the defect returns.

1. Set `status`, `closed`, and **`guard`** — the test that fails if it comes back. For a
   proposal whose outcome is a rule rather than a behaviour, set **`normative`** instead:
   the document that absorbed the durable rules. One of the two is required for
   `resolved`; neither is for `withdrawn` or `superseded`.
2. Move the document to `archive/`.
3. Close the issue with a comment naming the fix, the guard and the record.

**Archive, never delete.** A repository that deletes a closed entry breaks every reference
into it.

## Labels and milestones

| group | labels |
| --- | --- |
| kind, exactly one | `bug`, `proposal`, `enhancement`, `documentation` |
| state, zero or one | `in-progress`, `blocked`, `partial` |
| triage | `needs-triage`, set by hand on arrival from outside |

The **`post-1.0` milestone** carries the deferral. It replaces nothing: the `post_1.0/`
subdirectories stay, and the milestone makes the same fact visible from the board.

## Where we differ from MolSysMT

Two deliberate differences, both about what belongs in a queue:

1. **Only single-theme reports live in `pending_*`.** Plans and inventories do not: the
   pre-1.0 master plan and `what_needs_a_human_2026_08.md` sit at `devguide/`, and the two
   audit inventories in `devguide/audits/`. An issue for an eleven-phase plan would be an
   issue that never closes.
2. **We have no generated indexes and no `devguide_issue.py` yet.** The front matter and
   the issues came first on purpose; a validator written before the data exists is written
   against a guess. `tests/test_reporting_protocol.py` checks the parts that are cheap to
   check today.

## The asymmetry

It holds in one direction only:

- **Every document in the two queues has an `issue`.** Always.
- **Not every issue has a document.** One arriving from outside has none until it is
  triaged, and one that cannot be reproduced closes with the reason and never gets one.
