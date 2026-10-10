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
retained in the receipt. Source integration is complete; hosted CI closure is recorded below.


## Integration checkpoint

Reviewed source is pushed directly to main in
`792fd5f6baea34dd11016854ace78d76d5d087c6`. #218–#222 are closed with the fix,
addressable guards and archived records. The 27 active queue documents agree
with the issue board, and unrelated sandbox work remains outside integration.

At the recorded observation, Ruff `38046731008` and publication governance
`38046731328` pass. Notebooks `38046731029` is in progress; scientific CI
`38046730917`, source pair `38046731092`, core browser `38046731000` and suite
policy `38046731297` are queued. No terminal result is inferred for active runs.
The source candidate stays unfrozen and both 1.0 publications remain paused.

## Hosted CI review

The follow-up reviews the existing automatic runs for the exact source commit
above. Ruff, suite policy (including formatting), publication governance and
documentation notebooks pass. Core browser run `38046731000` passes **43/43**
suites with real Mol*/Chromium; Linux/Python 3.13 also passes **325/325** JS unit
tests and their coverage execution.

In scientific run `38046730917`, Linux/Python 3.11, 3.12 and 3.13 each pass
**3037 tests, 35 skips**, with no failures. The three macOS/Python 3.11–3.13
jobs remain queued without assigned runners at this checkpoint. They have not
run and cannot be counted as passed. The separate Qt job fails before obtaining
a WebGL canvas; the later render step is skipped. This observation is retained
in uibcdf/molsysviewer#109's maintained record. The workflow is not globally
green, and its queued state is not a completed scientific result.

Source-pair run `38046731092` uses MolSysMT
`46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`. Its Windows/Python 3.14 cell passes
**3011 tests, 61 skips**, and macOS/Python 3.14 passes **3010 tests, 62 skips**,
plus the installed-source native path and integration guards in both cells.
Linux/Python 3.14 passes **3037 tests, 35 skips**, its native/integration
guards, **43/43** core browser suites and **25/25** documented notebooks. The
source-pair run completes successfully in **3/3** cells. Platform-specific, optional Qt and artifact-dependent
skips keep their reported scope; these source runs do not qualify canonical
staged archives.

The receipt's `hosted_ci_review` preserves run/job identities, step outcomes,
original metadata and log digests. No source fix is indicated by the completed
core observations. No run is duplicated or cancelled, no provider reference
moves, and no release or candidate freeze is authorized by this review.


At that checkpoint, the applicable review remained **partial** because the three scientific
macOS/Python 3.11–3.13 cells still have `runner_id=0` and no assigned runner at
the recorded inspection. No currently running Viewer scientific cell remains
outside those queued jobs. Those cells are preserved in the original run,
without cancellation or rerun. Finishing their observations requires GitHub
runner assignment; the green Python 3.14 macOS cell does not replace them.

The updated reporting, link and architecture checks pass **230/230** locally.

### macOS completion

In the original run and attempt, macOS/Python 3.11 job `114197659939`
completes successfully: **3010 passed, 62 skipped, zero failures**, with its
original log retained and digested in the receipt. Its runner was assigned at
11:39:42 UTC and the job completed at 11:50:53 UTC on 2026-10-10.
Python 3.12 job `114197659937` and Python 3.13 job `114197659960` also complete
successfully in that original run and attempt. Each reports **3010 passed,
62 skipped, zero failures**. Their original logs and final run metadata are
retained with digests in the receipt. There is no duplicate execution, rerun
or change to the tested source.

The applicable scientific review is now **complete: 6/6 cells pass**, alongside
the successful Python 3.14 source pair, browser, JS, notebook and governance
gates described above. No macOS observation remains pending. GitHub's overall
workflow conclusion is still `failure` because of the experimental Qt job;
the six passing scientific cells do not turn that workflow green. Its two
control/PR jobs are skipped as expected for this push. This closes source CI
review, not canonical installed-artifact qualification, candidate freezing or
publication. Both 1.0 publications remain paused.
