---
summary: Receive independent MolSysMT chemical domains through Viewer and the expert addon.
issue: uibcdf/molsysviewer#269
status: blocked
opened: 2026-10-29
closed:
verification: measured
area: [molsysmt, loading, interactions, addons]
guard:
normative: devguide/chemical_domain_receiving.md
blocked_by: [uibcdf/molsysmt#533]
supersedes: []
---

# Current ChemicalStates source receiving

## Follow-up — 2026-11-03

The provider refactor #255 is merged and closed; the remaining installed-export
defect now has its own owner, uibcdf/molsysmt#533. Committed main
`bd28d57f2b0b31a6215d206dea27602f5f72e70d` still expects 101 private exports
while Rust registers `get_vectors` as the 102nd. No matching repair issue existed
outside the completed refactor discussion. Keep the exact export guard active
and wait for an identified correction before repeating the installed matrix.

The latest provider commit adds typed component-label preservation during
extraction. An isolated archive of its committed package/addon sources excludes
the sibling's unrelated work. With the unchanged shared native backend (Rust
sources match the previously received checkpoint), 164 directed Viewer cases
pass without skips, including all five protected-copy cases, loading, hierarchy,
composition, atom/structure correspondence, extraction, sessions and interactions.
This is scoped source receiving, not a new build or installed qualification.
An independent public `View.extract` probe also preserves literal `string`
label dtypes, values and null masks for a complete CC component, with the
source labels unchanged; it is separate from the 164 pytest cases.
The [follow-up receipt](../chemical_domain_receiving_20261103.json) retains exact
sources, backend hash, selection and original JUnit.

The three original JUnit files from current public-baseline source run
41667711485 all retain exactly the known three Pandas4Warning documentation
failures. Seven new coverage controls pass on each platform. General CI's
Linux 3.14 job likewise passes all 335 JS cases and fails those same three
Python examples. Its independent policy failure is formatting of the new
coverage guard, corrected without changing assertions. No warning suppression,
provider-source edit, new minimum or candidate publication is introduced.

## Previous receiving — 2026-11-02

The [operational contract](../chemical_domain_receiving.md) owns runtime state
selection and missing-domain semantics. The [dated receipt](../chemical_domain_receiving_20261102.json)
holds exact source identities, commands/scopes and original-result digests.

At provider `de7ffad2aef18ff3bccd184133dc69e081cb506e`, the implemented Viewer
adaptation has 265 affected core cases and five independent-copy cases passing
locally. All 2,453 addon nodes pass across the original run and one cwd-corrected
selective recovery, not a fresh complete invocation. No renderer or provider
compatibility facade is introduced. Source copying is received separately in
the archived #259 record.

Exact Viewer `481319a9` / provider `de7ffad2` source matrix 41577620754 fails on
Linux/macOS/Windows before science: the newly installed Rust extension exports
`get_vectors`, absent from the provider's reviewed manifest. Original job logs
confirm the same failure; it is reported to MolSysMT#255. Keep the native guard
active and wait for an identified provider repair rather than filtering exports
or repeating unchanged inputs.

Receive the corrected immutable provider source, review its actual diff, then
execute/inspect the applicable exact source-pair gates. Preserve the earlier
public-0.23.0 Pandas4Warning failures as their own dependency context. Return
actual sources, results and remaining limitations to #269 and MolSysSuite#155
at closeout. Installed artifacts and later release qualification remain separate;
neither a complete local selection nor an upstream closure certifies them.
