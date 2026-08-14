---
summary: Decide whether the evidence labels govern the whole devguide or only the capability audit.
issue: uibcdf/molsysviewer#61
status: open
opened: 2026-08-14
closed:
verification: measured
area: [docs, process]
guard:
normative:
blocked_by: []
supersedes: []
---

# Evidence labels beyond the capability audit

**Raised:** 2026-08-14, while adopting MolSysMT's reporting protocol. The labels landed on
19 rows and stopped there, deliberately. This records why, and what would have to be true
to extend them.

## What exists now

`devguide/capability_audit.md` carries an `Evidence` column with five labels:

| label | meaning | source |
| --- | --- | --- |
| `implemented` | the code path exists and is reachable from the public API | derived |
| `contract-tested` | Python tests exercise the documented behaviour | derived |
| `browser-observed` | an E2E suite drives it in a real browser and asserts what it drew | derived |
| `benchmarked` | a reproducible benchmark records environment and methodology | declared |
| `human-observed` | someone has watched it on a real screen | declared |

Four of five are **derived** from what the audit already knows. Only two are declared, and
both must name where the evidence is: a benchmark points at a document that must exist,
and a human observation carries its date.

They are adapted, not copied. MolSysMT's `Parity-tested` and `Scientifically validated`
are absent because they are MolSysMT's questions — comparing equivalent forms, comparing
against an independent oracle. A viewer renders what MolSysMT computes, so its equivalent
question is *did anyone watch it draw*, and that is the one that has caught real defects
here.

## Why it matters that they stopped there

The problem the labels solve is real and not confined to 19 rows. One round of auditing
found **five devguide documents asserting states the code contradicted** — including one
that criticised exactly that failure while committing it. Every document outside the audit
still declares its own state in prose.

## Why extending them is not obviously right

**A half-applied vocabulary is worse than none.** With labels on some documents and not
others, an unlabelled document reads as *"not verified"* or as *"nobody has got to it
yet"*, and a reader cannot tell which. The current state is honest precisely because the
boundary is sharp: one generated document carries them, and nothing else claims to.

**Most devguide documents are not about a capability.** Contracts, architecture records,
performance measurements, plans and audits are the bulk of it. `browser-observed` says
nothing about `scene_contracts.md`. Forcing a vocabulary designed for capabilities onto
documents that are not about capabilities produces labels that mean "not applicable",
which is the failure mode that made us drop two of MolSysMT's five in the first place.

**Derivation does not survive the move.** The audit's labels are cheap because the audit
already knows the tests and suites per capability. A hand-written label on a contract
document would be an assertion — the exact thing the audit exists to replace.

## What would have to be true

The extension is worth doing if, and only if, someone can name:

1. **Which class of document it applies to**, such that the rest is out by definition
   rather than by omission. "Documents that describe a capability" is a start and is not
   yet a rule someone could apply without judgement.
2. **Where each label would be derived from**, for that class. A label that must be typed
   by hand will age exactly like the prose it replaces.
3. **What an unlabelled document in that class means** — an error, or a state.

If those three cannot be answered, the honest outcome is the opposite decision: state in
`DOCUMENT_POLICY`-equivalent terms that the labels belong to the capability audit alone,
and that every other document says what it knows in prose and is checked by the guards
that already exist. That is a real answer and closes this.

## What was refuted

**"Copy MolSysMT's five labels."** Two of them cannot be earned here, and a vocabulary
carrying two permanently inapplicable values teaches readers to skim it.

**"Put the labels in the front matter of every devguide document."** Front matter is
already adopted for the two work queues, so this looks free. It is not: a queue entry's
`verification` qualifies *a report*, and evidence labels qualify *a capability*. Putting
both in the same header on documents that are neither invites exactly the confusion the
capability audit's *Two columns, two questions* section exists to prevent.

## Related

- [`capability_audit.md`](../capability_audit.md) — where the labels live and what they
  currently say, including the four capabilities nothing has watched draw.
- [`reporting_protocol.md`](../reporting_protocol.md) — the `verification` field, which is
  the other axis and must not be conflated with this one.
- MolSysMT's `devguide/DOCUMENT_POLICY.md` — the canonical version, `uibcdf/molsysmt`.
