---
summary: Classify optional keyword insertions by preserved Python call bindings.
issue: uibcdf/molsysviewer#352
status: resolved
opened: 2026-11-10
closed: 2026-11-10
severity: low
verification: reproduced
area: [public-api, compatibility, tooling]
guard: tests/test_public_api_contract.py
normative: docs/content/developer/public_api.md
blocked_by: []
supersedes: []
---

# Optional keyword compatibility

The initial F1 classifier recognizes appended optional parameters only. B4's
optional keyword-only `observations=None` precedes the existing digest flag,
so the report labels it breaking even though every old parameter/name/default
and old Python binding is unchanged. All declaration drift still fails; this
is an inaccurate diagnostic rather than a compatibility escape.

The unchanged implementation fails the new real `inspect.Signature.bind`
control in private receiving 214. Improve optional insertion/reordering while
retaining removals, changed defaults/kinds and positional or variadic semantic
shifts as incompatible. The report does not prove scientific return semantics.
The current reviewed API baseline must not be regenerated to hide this case.

Related: original #350 and B4/#349 under #315. A scoped open/closed issue search
found the original snapshot and unrelated documentation binding reports, but
no specific report of this comparison limitation.

## Resolution — 2026-11-10

The comparison now proves old parameter records unchanged, positional bindings
preserved and optional additions admissible. Keyword-only insertion and
reordering are reported as compatible changes while still failing drift
review. A positional addition cannot consume an old `*args` value or move an
existing positional argument; required additions, removals and default/kind
changes remain incompatible. Other unsupported change patterns stay
conservative; this is not a scientific semantic-compatibility solver.

Private 214 preserves the failing real Python binding control before the fix.
The complete API-contract/inventory selection then passes 32 cases in 215, including
independent positional, variadic, required-keyword and keyword-only ordering
controls. The reviewed 954-declaration baseline is unchanged by this fix.
B4's independently reviewed optional keyword remains its own intended API
addition; its [receipt](../figure_observation_receiving_20261110.json) preserves
the initial diagnostic and this follow-up. Publication remains paused.

The final review also exposes a second variadic case in 227: a newly named
keyword consumes a value previously bound inside existing `**kwargs`. The
comparison now rejects those additions conservatively. An independent positive
control preserves positional-only additions whose same-name keyword still
belongs to `**kwargs`. The final 25-case contract/digester-caller selection
passes in 229; 228 preserves a usage error from a mistyped test path with no
execution. No API baseline changes accompany this diagnostic correction.
