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
blocked_by: [uibcdf/molsysmt#255]
supersedes: []
---

# Current ChemicalStates source receiving

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
