# Guidelines for AI agents working in `devguide/`

This file refines the repository root `AGENTS.md` for this directory. Where the two
disagree, the more specific one wins; where this one is silent, the root applies.

## Read the current guide. Read the history only for a stated reason

`devguide/` holds two kinds of document, and only one of them is ordinary reading.

**Current** — the contracts, the engineering rules, the reporting protocol, the plans in
flight, the performance baselines and the direction documents. When someone asks you to
read the devguide, this is what they are asking for.

**History** — [`archive/`](archive/README.md) and [`audits/`](audits/README.md):
completed implementation plans, resolved defect reports and closed investigations. They
are evidence, not instructions. **Do not read them to find out what the project does**,
because by definition they record what it did. Whatever survived from them is already in
the contracts, and the contracts are what the code obeys.

Each of the two carries an index, and reading the index is the whole of the required
reading:

- [`archive/README.md`](archive/README.md) — one line per archived document, saying what
  it delivered or resolved.
- [`audits/README.md`](audits/README.md) — the closed investigations retained as evidence
  for current contracts and guards.

Together they cost 61 lines. The documents they index cost 6,583, which is 23 % of this
directory, for conclusions that have already moved somewhere normative.

### What counts as a reason to open one

A reason is a specific question that only that document can answer, and it is named
before the file is opened. Four recur:

- **a current document points there for its rationale.** The contracts do this on
  purpose, so that a rule is not obliged to carry its own history.
- **a decision is being reopened**, and what it cost to take — the measurements, the
  paths refuted — is in the archive rather than in the rule it produced.
- **a claim needs its evidence**: a benchmark, a mutation ledger, a version checked on a
  date.
- **a defect looks familiar**, and the archived report says whether it is the same one
  and what closed it.

"To be thorough" is not a reason, and neither is "to understand the project". If a fact
about current behaviour exists only in the archive, the contract that should hold it is
incomplete — report that instead of absorbing the archive.

### The corollary that keeps this rule honest

**A document is archived and indexed in the same change.** An index that does not list
everything turns this rule into a silent omission: a reader who trusts it concludes there
is nothing else, and the unlisted document becomes unreachable rather than merely unread.

`reporting_protocol.md` already requires archiving over deleting. Indexing is the other
half of it, and leaving the two to agree by good intentions is the drift pattern this
whole directory is built against.

## Deferred is not historical

`pending_bugs/post_1.0/` and `pending_proposals/post_1.0/` are **not** covered by the
exemption above. Deferral is a scope decision about work that has not happened, so those
documents describe intent that still stands. Their queue READMEs are generated from front
matter by `python devtools/devguide_index.py`; whether an entry itself needs reading
depends on the work at hand, not on a blanket rule.

## Writing in this directory

`README.md` §Maintenance rules is normative for anything added here: say "done" where a
scan will hit it, keep a closed item to one line, and write the sentence rather than the
bullet list when the bullets carry one idea each.
