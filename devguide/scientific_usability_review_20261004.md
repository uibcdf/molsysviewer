# Scientific usability follow-up — 2026-10-04

## Observations and corrections

A real JupyterLab notebook in `molsyssuite@uibcdf_3.14` (Python 3.14.7)
rendered pentalanine with local frames extracted in order `[0, 8, 3]`. Studio's
query preview resolved `atom_index==5` but did not activate it for staging
(#158). Staging the same atom through Selection exposed a second defect:
display A was silently reused as calculation scope (#159). A whole-system
Buch calculation at 4 Å has 20 observations in frame zero; one is incident to
atom 5, whereas a calculation restricted internally to atom 5 has zero.

Both consumer defects are corrected. Interactions uses the existing public
selection owner after a correlated successful preview, and calculation defaults
to all atoms with separate explicit A/between-A-B options. Display filtering
leaves the stored scientific analysis intact. Scientific dispatch stays in
Python/MolSysMT. The normative rule is in `scene_contracts.md`; the resolved
records are [#158](archive/interactions_query_dock_cannot_stage.md) and
[#159](archive/interactions_display_filter_changes_calculation.md).

The final real-Mol* browser lane checks query staging, stale replies, missing,
overlapping and unsupported scopes, all-atoms 20-observation calculation with
one displayed occurrence, explicit A and between calculations, and all 17
existing forms across nine families. It passes in **155.557 s**, without skip
opt-out or deadline override. The bounded browser selector profile is recorded
in `reporting_protocol.md` and mechanically checked by the Python protocol tests.
No correctly constructed Python request is substituted for a browser emission
guard.

The once-run complete source regression passes **2,812 tests, 23 skipped**
in **606.81 s**. The protocol module and all five loading-identity cases pass
their targeted runs; Ruff, TypeScript and the official runtime rebuild pass.

## Provider integration received during the review

MolSysMT closed uibcdf/molsysmt#312/#313 at `577d0ab32`, present in the local
checkout. Direct SDF loading now accepts caffeine (24 atoms). Real 1VII plus
caffeine loads successfully both progressively and in one batch (596 + 24 =
620 atoms). Atom coordinates agree exactly; both sources and base-region records,
scene state, region undo/redo and MSV sessions survive. The existing five-case
identity-prevalidation guard also passes its successful provider branch.

Its malformed negative fixture had assumed out-of-range group membership must
raise. The repaired provider resolves that to missing identity; the test now
uses ambiguous duplicate group keys to exercise failure and preservation. A
dated correction is appended to the immutable #157 archive. Product
prevalidation has not changed and no MolSysMT files were modified here.

## Evidence and limits

The machine receipt is `scientific_usability_review_20261004.json`. Temporary
notebook, screenshots, logs and the mixed-source driver are under
`/tmp/msv-usability-review-20261004`; product browser guards remain in the repo.
The notebook host produced an unrelated debugger page error and, during repeated
setup attempts, an ipykernel pending-task warning. Its screen observations do
not claim host-wide console cleanliness. The separate product E2E lane asserts
an empty page-error list.

The composed sources keep their original coordinate origins and the first-source
box, with explicit box/structural-attribute warnings. Successful composition does
not establish a physically prepared complex, alignment, suitability for PBC or
chemical preparation. The repaired provider is editable, has independently
changing unrelated work, and is not a frozen published dependency artifact.
Mixed-source Python/session qualification is not a new mixed-source browser or
full hosted-core certification. Compatible published dependencies, exact artifact
and hosted gates, final public documentation and broader user observations
remain before 1.0. No tag is created.

## Hosted integration follow-up

The reviewed source was committed and pushed without a skip marker at
`c598d2f2bde13215c367fd8f4f79fd0fff20fc3e`; #158/#159 are closed and 45
queue documents agreed with the board. Ruff lint and Conda governance passed.
The policy run [37191306848](https://github.com/uibcdf/molsysviewer/actions/runs/37191306848)
failed only its formatting step: 88 existing Python files needed the pinned
Ruff 0.16.5 formatting. They are now automatically formatted; ASTs before and
after are identical for every changed file, and formatting/lint checks pass.
The original functional regression remains applicable to these cosmetic changes;
its source identity and hashes are retained rather than rewritten. The formatting
receipt is `format_policy_followup_20261004.json`.

The notebook run [37191306553](https://github.com/uibcdf/molsysviewer/actions/runs/37191306553)
executed 24 notebooks and failed two: the Interactions workbench requires a
compatible published provider (#114/#140), and the Whole get notebook still
advertises query strings for the index-only mask argument. The latter is now
tracked in [#160](archive/documented_whole_mask_queries.md) for the agreed
final documentation block; public notebook sources are not changed here.
These hosted failures remain failures, separate from the passing local scientific
and browser observations. Other hosted lanes were still running at inspection;
no full hosted-head certification is claimed.
