---
summary: Receive independent MolSysMT chemical domains through Viewer and the expert addon.
issue: uibcdf/molsysviewer#269
status: active
opened: 2026-10-29
closed:
verification: measured
area: [molsysmt, loading, interactions, addons]
guard:
normative: devguide/chemical_domain_receiving.md
blocked_by: []
supersedes: []
---

# Current ChemicalStates source receiving

## Corrected installed-source campaign — 2026-11-03

The identified provider repair is now under consumer qualification in the single
[source-pair run 41690488611](https://github.com/uibcdf/molsysviewer/actions/runs/41690488611):
Viewer `d72f93f7aa8a3d89b2848bef905a48a00102f8e1` and MolSysMT
`d8ea626a0ab6dbd976d0e04ad9299019e4ae0a42`, Python 3.14 on Linux, macOS and
Windows. `source_receiving=true` skips candidate-version tagging and retains
ordinary installation, exact Rust-export validation, integration/core tests
and Linux browser/notebook execution. The
[campaign receipt](../chemical_domain_installed_receiving_20261103.json) owns
observed state and original-result digests. No result or closure is inferred
from dispatch. MolSysMT PR #538 remains independently owner-reviewed and is not
part of this provider source.

The Linux Python selection passes 3,347 cases with 25 skips; Windows passes
3,320 with 52 skips and completes its whole cell successfully. Both execute all
five protected-copy cases. Linux's 25 notebooks also pass. The original Linux
job nevertheless fails in the first browser suite: its positive pentalanine
fixture assumes a chain assignment that the legacy file does not declare.
The menu truthfully reports the missing membership. Test-only correction
`383721ea` declares one chain explicitly for both the snapshot and real-owner
request replay, leaving unknown/partial membership scenarios and all behavioral
assertions intact. The affected suite and the complete 44-suite core lane pass
locally with the exact provider snapshot and unchanged reused native backend.
All 3,420 archived package files remain byte-identical after those checks.

The hosted Linux failure remains recorded separately from local recovery.
macOS now completes its full cell: 3,320 Python passes, 52 skips and all five
copy cases executed. Its original JUnit and installed Rust result (102 exports,
minimum image 2.5) are received in the campaign record. The original three-host
Python scope is therefore complete; the full run remains failed on Linux's
browser fixture. Keep the issue active pending hosted Linux recovery.

The source-pair workflow now permits a whitelisted single-platform source
recovery while retaining all three platforms by default. Candidate mode rejects
a reduced platform set. Seventeen workflow guards cover both the matrix and
the actual Bash scope check; no Linux installation, audit, Rust, integration,
Python, browser or notebook step is removed. Recovery uses the same MolSysMT
commit so the successful original macOS/Windows receipts remain applicable.
No release or preserved-artifact gate follows from this source recovery.

The single hosted recovery is dispatched as run
[41714550124](https://github.com/uibcdf/molsysviewer/actions/runs/41714550124),
Viewer `c1137ebb21812c15d941fa3c5154bd655e329f85` against the same provider.
GitHub expands exactly one Linux job; the default push still expands all three
platforms. The recovery is queued with no executed steps at receipt. Independent
downloads verify all three original ZIP digests and exact JUnit bytes. These
integrity checks do not turn the original browser failure or queued recovery
into success; #269 remains active.

The previous recovery 41707479800 is cancelled and retained after the local
full regression identifies two distribution guards that still parse the former
YAML syntax. Commit `c1137ebb` reads the actual JSON default without relaxing
the three-platform assertions, and selects TAP explicitly in real coverage
probes. Nineteen matrix/distribution guards and seven coverage controls pass.
Replacement 41714550124 is dispatched only after the old run is terminal;
its production runtime is unchanged and excludes the independent #291 work.

## Follow-up — 2026-11-03

**Provider update:** published correction
`2797c5425f5735568422325928520ae591c3676a` adds the reviewed vector export and
guards actual-module drift. MolSysMT#533 retains the focused source and local
noneditable Linux evidence; its broader hosted qualification remains pending.
The original failure below remains preserved; the corrected campaign above
uses the new identified input rather than repeating the original provider.

The provider refactor #255 is merged and closed; the remaining installed-export
defect now has its own owner, uibcdf/molsysmt#533. Committed main
`bd28d57f2b0b31a6215d206dea27602f5f72e70d` still expects 101 private exports
while Rust registers `get_vectors` as the 102nd. No matching repair issue existed
outside the completed refactor discussion at the time of that attempt. The
exact export guard remains active in the corrected campaign.

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
