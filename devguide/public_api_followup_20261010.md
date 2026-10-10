# Public API follow-up — 2026-10-10

The principal maintainer authorized implementation after the second API review.
This is source work from `a8e0a9be`; it does not freeze 0.25.0 or authorize
either 1.0 publication. Unrelated sandbox work is preserved.

## Scope

| Issue | Correction |
| --- | --- |
| uibcdf/molsysviewer#218 | Intersect system-query atom selections and masks with the region; preserve global structural attributes. |
| uibcdf/molsysviewer#219 | Reject retired molecular and layer membership queries after deletion, undo, import or tag reuse. |
| uibcdf/molsysviewer#220 | Add digested `Region.set_mode`; mode assignment shares its history. |
| uibcdf/molsysviewer#221 | Declare the actual Annotation/Measurement return types and resolve Layer membership hints. |
| uibcdf/molsysviewer#222 | Expose detached filter/style properties; retain owned internal state for projection, remapping and restoration. |

Maintained behavior is in [scene contracts](scene_contracts.md#public-query-and-configuration-follow-up)
and the [public API reference](../docs/content/developer/public_api.md).
No provider source, frontend protocol or generated runtime changes.
Interactions remains experimental; the broad documentation round comes later.

## Verification

The new real-dialanine boundary module passes 13 cases: scope, global box/time,
six retirement/bypass combinations, mode history, recipe eligibility, runtime
typing and detached visual configuration. Legacy damaged-filter tests now
inject damage into exported state before importing it, preserving the intended
repair and migration checks through the public persistence boundary.

Related guards pass **310/310**. The single full Python execution reports
**3056 passed, 9 failed, 23 skipped**, exit 1 in 113.84 s. Eight failures are
known experimental Qt transport/generation/context probes. The ninth is an
older tools test deliberately pinning whole-system atom counts from a region;
#218 supersedes that policy before 1.0. Its corrected tools module passes
**14/14**. The full run is preserved and not repeated or called globally green.

The regenerated inventory contains **727/727** digested public callables,
442 declared argument digesters, no missing bypass arguments, no missing
handlers and no exemptions. Ruff lint and formatting pass across the repository.
The format check also corrects three files rejected by the previous source CI
`38045100550`; that failed historical result is preserved.

Development uses `molsyssuite@uibcdf_3.14` (Python 3.14.7). MolSysMT is a sibling
source checkout being advanced by its owner; `3347a108a19177482dcab4bd73a02374c960cd5e`
was observed during this execution. This is development-source evidence, not a
frozen provider or clean installed-pair qualification. Source evidence does not
qualify any staged archive. Experimental Qt remains outside the 1.0 core gate.
The [receipt](public_api_followup_receipt_20261010.json) records results and log
digests. Reporting, link, architecture, capability and inventory guards pass
**452/452** after correcting receipt creation and staging the archived reports.
Two preceding scoped checks stopped on those bookkeeping errors; both logs are
retained in the receipt. Source integration and new applicable hosted CI remain
pending.
