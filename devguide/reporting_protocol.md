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

## Filing one

Start from [`templates/report.md`](templates/report.md). **Open the issue first**, to
obtain the number: a document whose `issue:` still says `#000` fails the guard, and one
committed before the issue exists leaves the issue naming a path that is not on `main`
yet.

For a report that arrives from outside, the issue already exists and someone else wrote
it, possibly with the wrong diagnosis. Attending it means writing the local document and
answering once, restating *What / How / Why* **in our own terms** — that restatement is
the point of the comment, not a courtesy. Then remove `needs-triage`, and let the
document's `verification` field record whether we reproduced it, only inspected it, or
could not reproduce it at all.

## Corrections

A claim that turns out to be false is corrected, not left standing. Where depends on the
document's state:

- **In a queue:** correct in place. The document is live.
- **Archived:** append a dated correction note. **Do not edit the original claim.**

```markdown
## Correction — 2026-08-13

The section above states that `add_pharmacophore_features` was broken for positional
callers by the ArgDigest var-positional defect. It was not: it forwards to
`add_interaction_sites`, which is keyword-only, so a positional call was never possible
and fails identically with digestion bypassed. The `TypeError` measured was the target's
own binding. The report's other evidence — the three region booleans — was correct.
```

That example is real, and it is why this section exists. Rewriting an archived document
destroys the record of what we believed and when, which is the thing an archive is for. A
stale benchmark number needs no correction at all — it was true on its date. A claim that
was **never** true does.

## Security

An exploitable finding is not opened as a public issue. It goes to a
[private security advisory](https://github.com/uibcdf/molsysviewer/security/advisories/new),
and the local document stays out of the queues until a fix is released. This protocol
resumes at that point.

The advisory route is offered in `.github/ISSUE_TEMPLATE/config.yml`, so a reporter meets
it before the issue form.

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
2. **Our archive stays flat, and that is a decision.** MolSysMT splits it into
   `resolved_bugs/`, `resolved_proposals/` and `withdrawn_bugs/`. Considered on
   2026-08-14 and declined: they archived *into* that shape from the start, we would have
   to migrate 28 documents, and moving them breaks references — which is the very
   argument this protocol makes for issue numbers over paths. The gain is navigation
   comfort in a directory that is read by search, not by browsing. If it ever does become
   a problem, the answer is a generated archive index, not moved files.

3. **Opening and closing on the board are done by hand.** `devtools/devguide_issue.py`
   only ever writes the derived state labels; the two comments the protocol specifies are
   where the judgement is, and a script would write them badly.

## Indexes are generated

Each queue README has a hand-written head — how to read the directory, what precedence it
carries, what it demands — and a block rendered from front matter:

```markdown
<!-- generated: devguide_index -->
...
<!-- /generated -->
```

```bash
python devtools/devguide_index.py           # write
python devtools/devguide_index.py --check   # fail if stale
```

`--check` runs in the suite. A hand-written index of documents that already describe
themselves is two independent authoritative lists, and ours was the wrong one: it went on
describing four documents as queue entries after they had been moved out.

## Checking the board against the front matter

The front matter and the board are maintained by different acts — editing a file, and
clicking on GitHub — so they will drift. Nothing in the suite can catch it: verifying an
issue needs the network and a token.

```bash
python devtools/devguide_issue.py sync --check   # report drift, exit non-zero
python devtools/devguide_issue.py sync           # apply the derived state labels
```

Run it before a release and after any session that closed or restatused an entry. It
reports a document whose issue is missing, closed while the document sits in a queue, or
carrying a state label that disagrees with `status`. The last of those it can repair; the
others need a person, because either the document should have been archived or the issue
should not have been closed, and only a human knows which.

Narrative about a closed entry belongs in that entry's own `## Resolution` section, where
someone will look for it in a year — not in the index of a directory it has already left.

## The asymmetry

It holds in one direction only:

- **Every document in the two queues has an `issue`.** Always.
- **Not every issue has a document.** One arriving from outside has none until it is
  triaged, and one that cannot be reproduced closes with the reason and never gets one.
