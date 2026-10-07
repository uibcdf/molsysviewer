# Development checkpoint

This is the current handoff. Normative behavior remains in the linked contracts;
previous qualification records retain their original candidate and environment.

## Resume in one page

**0.24.0 stabilization published (2026-10-07): public pair 16/16 verified.**
Viewer **`1a4c97a58b68b69f3a836546c9e4ac6187c3efa2`**, noarch **build 1**, pairs
with MolSysMT **0.23.0**, **build 0 ABI3**, commit
**`46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`**. The provider's fixed branch
`candidate/0.23.0-build0` enables exact dispatch. All **16/16** installed staging
cells pass in [37541876875](https://github.com/uibcdf/molsysmt/actions/runs/37541876875).
Independent reads verify all sixteen actual environment ZIPs/digests, package
coordinates, hashes and staging repodata. Native Windows launchers pass in
[37542333568](https://github.com/uibcdf/molsysviewer/actions/runs/37542333568), bound
to the same Viewer commit, version, build and file SHA-256. All **39/39** hosted
core browser suites pass in [37541292806](https://github.com/uibcdf/molsysviewer/actions/runs/37541292806).
The six Linux/macOS Python 3.11–3.13 regression cells pass; aggregate CI still
fails on the separate experimental Qt/WebGL job (#109).

The provider's final-source gate
[37577738386](https://github.com/uibcdf/molsysmt/actions/runs/37577738386)
passes all eight Linux/macOS Python 3.11–3.14 cells with the exact final Viewer
commit. Independent downloads verify sixteen artifact digests, eight scientific
certificates (54/54 cases each, zero failures/errors/skips, clean exact provider
source) and eight JUnit reports (13,323 cases each, zero failures/errors).
The full-suite optional/environment omissions remain 26 on Linux and 27 on
macOS, with their reasons retained. The controlled Viewer wheel has development
version metadata; this gate supplies source integration evidence. Canonical
0.24.0 source/wheel and the installed staging pair retain their separate checks.

The installed build 1 matches all 620 Viewer archive members and passes
`pip check`, **298 affected checks/one expected omission**, and **eight real
offline-export browser checks**. The ordinary corrected wheel also passes its
runtime/version validator. Build 0 and its original failed full/browser outcomes
remain recorded: temporary history tags and premature Movie completion are
resolved in [#171](archive/temporary_candidate_tags_change_release_history.md)
and [#172](archive/movie_done_precedes_final_canvas_draw.md).
[Source version handling](archive/automatic_source_pair_runtime_version.md) (#173),
[hosted control-job interpretation](archive/hosted_core_inactive_backlog_gate.md)
(#174), and [development runtime synchronization](archive/automatic_source_version_retags_development.md)
(#175) are developer-tooling corrections; the immutable package candidate
stays `1a4c97a5`. The initial #173 approach conflicts with an existing policy guard
and is preserved as refuted evidence. The correction at `d5ac10f0` passes
310 closure/policy/gate/link checks and eight real development offline exports;
automatic hosted follow-up [37545069147](https://github.com/uibcdf/molsysviewer/actions/runs/37545069147)
now passes on all three native hosts: Linux 2,893 cases/27 skips, macOS
2,866/54 and Windows 2,867/53, zero failures. Linux additionally passes all
39 core suites and 25 documented notebooks. These development-provenance
results complete the tooling correction without replacing the fixed package.

Canonical exact-source Python 3.14 integration passes in
[37542642197](https://github.com/uibcdf/molsysviewer/actions/runs/37542642197).
Linux passes 2,879 cases/27 skips, macOS 2,852/54 and Windows 2,853/53,
with zero failures; Linux additionally passes 39 core suites and all 25 notebooks.
The earlier public-channel CI failed before tests while MolSysMT 0.23.0 was
staging-only. Its [0.23.0 Release](https://github.com/uibcdf/molsysmt/releases/tag/0.23.0)
is now published at the exact provider commit. Independent downloads verify all
four public-package receipts, original SHA-256 values, `main` labels and
solver-visible indices. Its hosted documentation passes in run `37583385927`.
Provider source preservation is verified in run `37583715416`: the downloaded
receipt digest and public Zenodo API agree on version DOI
[10.5281/zenodo.23205366](https://doi.org/10.5281/zenodo.23205366), source ZIP
`uibcdf/molsysmt-0.23.0.zip` and `md5:9e2aa4844c6b8ef030b92dcca6bc7bd3`.
This supersedes the initial pending ingestion observation in the receipt;
source preservation does not claim package archival.
Diego explicitly authorizes Viewer publication on 2026-10-07. The canonical
`0.24.0` tag is pushed at the exact fixed producer. npm run `37584736989` fails
before build/publish because the qualified manifest already carries 0.24.0;
publisher recovery is tracked in [#176](archive/npm_publication_rejects_synchronized_version.md).
The corrected publisher in `493f6eb6` completes build/upload in run
`37586395370`; independent tarball integrity, version and byte-identical CDN
checks pass. The [Viewer 0.24.0 Release](https://github.com/uibcdf/molsysviewer/releases/tag/0.24.0)
is published from the unchanged tag. Conda promotion `37587274965` passes:
all receipt digests, original build-1 SHA-256, public `main` label and solver
index are verified; build 0 remains staging-only. Release route `37587205281`
omits both build/upload paths as required. The first promotion dispatch
`37587118096` fails before mutation while Release creation is rejected; both
observations remain in the receipt.
Viewer source preservation is verified in `37587205154` at version DOI
[10.5281/zenodo.23206053](https://doi.org/10.5281/zenodo.23206053). The downloaded
source ZIP checksum matches the receipt and public API. Its annotated-tag archive
root is verified, and 23 selected source/metadata files match the exact producer.
All **16/16 public installed cells** pass in
[37587631519](https://github.com/uibcdf/molsysmt/actions/runs/37587631519)
at the exact provider commit: four platforms and Python 3.11–3.14. Independent
downloads verify every environment ZIP digest and original public package
coordinate; all four required steps pass in each cell. The exact-source
`public_conda` release gate passes (one check, zero failures/blocked/exceptions).
This completes coordinated stabilization qualification; it does not clear 1.0.
The earlier devguide reconciliation passes 277 bounded checks;
its 45-report board snapshot precedes #176. MolSysMT confirms the exact candidates
and publication order in its evidence commit `832e01210`.
The bounded reports #114/#140/#151 are resolved: public qualification and
updated Interactions documentation are complete, with 207 fresh installed
scientific/loading checks passing. Their workflow follow-ups #142/#144/#145
are now also resolved: 47 fresh installed tests and five executable user-guide
blocks cover bounded pages, native H5MSM save and participant select/focus.
Design corrections #146/#147/#148 are resolved with 27 fresh installed tests,
twelve labels-guide blocks and a legacy-fingerprint re-resolution probe. Their
source/runtime remains the published baseline. The Movie interruption failures
on successors `513391c1` and `4bedcba9` remain preserved. #177 is now resolved
in source `7880e2e3`: stop restores the observed camera through a fresh Mol* draw,
with a unit mutation control and real native paused-draw browser guard.
Core [37680239149](https://github.com/uibcdf/molsysviewer/actions/runs/37680239149)
passes 39/39; exact-source pair
[37680239068](https://github.com/uibcdf/molsysviewer/actions/runs/37680239068)
passes on all three Python 3.14 hosts (Linux 2,879 passed/27 skipped, macOS
2,852/54, Windows 2,853/53), plus 39 core suites and 25 notebooks on Linux.
Standard CI `37680239319` passes six scientific cells but fails on experimental
Qt WebGL startup (#35). These source results do not replace the published
0.24.0 packages or clear final 1.0 recertification. See
[the Movie correction receipt](movie_interruption_fix_20261007.json).
#149/#150 are now resolved. The plot owner and its guards match the public
producer; twelve fresh installed finite-input/lifecycle checks and seven numeric
geometry/seeking units pass. Review of #149 finds a remaining nested applied
recipe alias in the public package. Source `027374ed` corrects it; checkpoint
`bd824ea1` and a controlled development wheel pass thirteen design guards,
runtime/version validation and pip check. Exact-source pair `37685753081`
passes Python 3.14 on all three hosts (Linux 2,876 passed/27 skipped, macOS
2,849/54, Windows 2,850/53), plus 39 core suites and 25 notebooks on Linux.
Independent core `37685752799` passes 39/39; six standard scientific cells pass.
The first formatting gate and the local sandbox full-suite failure remain
preserved, as does experimental Qt startup. This style correction is in source,
not the unchanged public 0.24.0 files. See
[the styles/plot closure](styles_plot_closure_20261007.json).
Plot lifecycle #143 is also resolved: six fresh installed guards and two guide
examples pass on the original promoted public-version pair. Owners and guards
match the published producer; existing 39-suite core evidence is reused. See
[the plot lifecycle closure](trajectory_plot_lifecycle_closure_20261007.json).
#101/#153/#154/#155 are also resolved: public Windows `37693319370` passes
exact build/digest and all three installed launchers; 49 fresh installed
CLI/worker/box cases, five launcher guards and seven runner guards pass.
Unchanged owners bind the existing scientific/core evidence. See
[the remaining partial closures](remaining_partial_closure_20261007.json).
The only partial bug report left is experimental standalone #35, outside the
core 1.0 gate; its failed hosted graphics observations stay preserved.
Next: reconcile broader public documentation and complete installed first-contact
and final-candidate review, carrying Movie #177 and styles #149 into the next
qualified artifact. Retain the completed public pair and publication checks.
See [the candidate preparation](stabilization_024_preparation_20261006.json).

**Published support-library receiving check (2026-10-06): bounded pass.**
Exact Conda SMonitor **0.19.0 `py_1`** and ArgDigest **0.15.0 `py_0`** pass
**122 installed checks, 14 expected skips** on Linux x86_64 / Python 3.14.8,
with a Viewer wheel from `6be2bcd272ef6eda014c4bb3cf6f50f04695e8ef` and
public MolSysMT 0.22.4. Archive/member hashes, isolated imports, runtime
version and `pip check` pass. Six new cold-import/reload guards preserve
application diagnostics and render a catalog without replacing its profile.
No runtime source, dependency minimum or capture default changes. The once-run
source regression returns **2,879 passed/23 skipped, two failed**: the offscreen
Qt transport/payload processes cannot initialize their OpenGL RHI, tracked
under experimental #109. This is not a full-suite pass. The receiving guard
and receipt are published at `a48478fc`; policy and Conda governance pass.
Its three-platform source-pair CI now passes; Linux also passes 39 core browser suites and all 25 documented notebooks. Compatible installed
scientific-pair staging qualification is now complete as recorded above;
public-pair and final 1.0 qualification remain pending. See
[the maintained adoption record](python_ecosystem_policy_adoption.md#published-support-library-receiving-check--2026-10-06)
and [the receiving receipt](support_library_receiving_20261006.json).

**Earlier qualified source handoff (2026-10-06): #160/#169/#170 resolved.**
Viewer **`d7939f08d604138112edfe84ccc9bc4a40428057`** with MolSysMT
**`a0ceca86ec99c89377e78fac15cbdf32145a362e`** passes source-pair run
[`37523291585`](https://github.com/uibcdf/molsysviewer/actions/runs/37523291585):
Linux **2,875 passed/27 skipped**, macOS **2,848/54 skipped**, Windows
**2,849/53 skipped**, zero failures. Installed-source origin/dependency/Rust
checks and real integration pass on all three platforms. Linux additionally
passes **39/39 core browser suites** (17 calculation forms, 10 geometry fixtures)
and **25/25 documented notebooks**. At that checkpoint this fixed pair was ready
for MolSysMT's coordinated staging preparation and superseded the earlier
c046fca/5e272169 handoff. The current stabilization pair at the top of this page
supersedes those source coordinates.

[#169](archive/source_guards_use_platform_encoding.md) fixes the six Windows
encoding failures with explicit UTF-8 reads and a guard. [#170](archive/source_pair_omits_scientific_workflows.md)
adds complete notebook/browser source coverage without changing the distinct
published/staging gates. [#160](archive/documented_whole_mask_queries.md) corrects
Whole masks to atom indices; its notebook also passes with the published provider.
Local validation includes 302 focused checks, 229 final archive/contract checks,
all 25 notebooks, 39 core suites and strict Sphinx. The once-run full local suite
has 2,883 passes/23 skips and one new-report Git-index failure corrected by staging
and targeted link checks. A moved archive link and one format-only hosted policy
failure are diagnosed and corrected; all 886 Python files pass formatting and lint.
The final source commit passes hosted MolSysSuite policy. These complete native
verdicts supply the later regression result; no second local full run is made.
See [the closure receipt](ci_workflow_closure_20261006.json).

Compatible installed-package qualification is still pending. Public notebooks
fail on the missing caffeine SDF and Interactions API, and public browser CI on
the absent H5MSM writer. The public Python matrix also lacks repaired loading/box
capabilities. Qt's hosted WebGL failure is already tracked under experimental
#109. No release tag, package promotion or strict 1.0 clearance is created.

**Human review (2026-10-06): the five-stage notebook walkthrough is complete.**
The initial protein displays correctly. Rotation, zoom, translation, context
menu/reset, both Help routes, full screen and its return, floating Studio
controls/docking/popup lifecycle and canvas-popup movement synchronization
are reported passing. Progressive caffeine loading displays both sources with
appropriate framing; the provider warnings are understood. It reveals a
transient Welcome card (#164) and lossy accented source-region tags (#165).
Both are now resolved in source: [#164](archive/welcome_card_flashes_during_system_rebuild.md)
uses an explicit pending-load state, and [#165](archive/automatic_source_regions_corrupt_unicode_labels.md)
preserves readable Unicode tags. All **39/39 core browser suites** pass.
The once-run Python suite returns 2,816 passed, 22 sandbox permission failures
and 23 skipped; normal pytest outside the sandbox passes those explicit 22
nodes. The full Python suite is not repeated. See
[the loading-fix receipt](load_usability_fixes_20261006.json).
Diego now confirms both corrections in the human review after the source fix
`66a924404feadaef7aa7147fea573533c21d40c8`. Studio base-region Hide/Show
and the section 2 Python API are reported passing. Own-region Hide reveals
Whole under the earlier contract. Diego approved #167: enabled Hide constrains
Whole in every representation state; enable/disable independently suspends and
reapplies visual configuration while preserving the hidden request. The API,
Studio, colors and scene lifecycle now have passing regression coverage. Diego
confirms the implemented Hide/Enabled behavior works after `845d34b6`. He agrees
to keep Python `show_only()` and Studio controls unchanged; no isolation button
or temporary-isolation redesign is added. Diego also confirms notebook section 3:
batch loading of protein and caffeine has appropriate framing and source regions,
Whole contains both, caffeine Hide/Show preserves the protein, and the exact
coordinate comparison cell passes. In notebook section 4 he confirms correct
pentalanine display and navigation across three frames. Interaction calculation
scope is under review: only the first frame says Evaluated; the others say Not
evaluated. Diego confirms leaving the default, believing it was `all`; Calculate
structures actually defaults to `current`, which explains the coverage pattern.
His supplied analysis metadata confirms one evaluated structure and zero
occurrences at 0.23 nm, rather than the planned 0.4 nm review cutoff. After the
explicit all-frame/0.4 nm guidance and returning from Stored analysis to Calculate,
Diego confirms visible H bonds specific to each structure, working Hide/Show,
frame-specific Inspect with participants/distances in nm, participant selection
and focus, and Inspect after a frame change. He confirms the structure display
filter, excluded-frame status, all-frame restoration and preserved analysis
counts work as proposed. Next is the Python reference and atom filter, then
session recovery. Record the scope/mode confusion as usability evidence; the
human has not transcribed exact new-analysis counts.
The naming discussion approves explicit query/display values in
[#168](archive/explicit_interaction_selection_mode_names.md):
involving_selection, within_selection, across_selection_boundary and
between_selections. Provider uibcdf/molsysmt#346 and consumer #168 are now
resolved in source, using provider `a0ceca86ec99c89377e78fac15cbdf32145a362e`.
The new full Linux Python run passes 2,869/23 skipped with zero failures;
322 Node 22 unit tests and the three affected browser suites pass, including
four display modes and 17 calculation forms. Version-1 saved display filters
migrate to extension 2; new public calls reject old names. Scientific coverage
metadata/H5MSM are unchanged. See [the receipt](interactions_query_modes_20261006.json).
The updated hosted matrix and installed-package gate remain pending. Diego
subsequently confirms that the change works and asks to proceed to notebook
section 5, Guardar y recuperar. Session/frame/filter/visibility restoration and
the distinction between complete sessions and analyses-only H5MSM are the next
human observations; the notebook remains untouched. Diego subsequently reports
that saving/reopening appears to work throughout the requested checks. This is
general recovery acceptance, without an exhaustive per-control record or a
separate independent-H5MSM reload observation. The five-stage human walkthrough
is complete. An unchanged snapshot is saved as
`sandbox/revision_pre_1_0_20261006.ipynb`, and his tutorial suggestion
is implemented in `docs/content/user/cookbook/molecular_workbench.ipynb`.
The new tutorial passes all 21 executable cells; the linked Interactions
notebook is refreshed, 29 static-runtime checks pass and the strict Sphinx
build succeeds. This review does not clear the distinct remaining 1.0
package/CI gates.
The separate [#166](archive/group_panel_unit_dom_missing_query_selector.md)
GroupPanel test DOM defect is fixed: the complete JS unit lane passes 322 tests.
[#167](archive/region_enablement_and_visibility.md) has 12 focused Python tests
and 264 passing selected follow-up tests. All 39 core browser suites pass
across 26 initial suites and a 13-suite follow-up after a stale tooltip assertion.
The once-run full Python suite returned 2,839 passed, eight failures and 23
skipped; diagnosed failures pass selected follow-ups, without a second full run.
[The enablement receipt](region_enablement_20261006.json) preserves these limits.
Keep these direct human
observations separate from automated evidence in
[the current review](human_usability_review_20261006.md).

**Previous coordinated source handoff (2026-10-06): validated before #168.**
Fixed Viewer commit `c046fca173f501c6e259761ef8f3d6b1825f17e8` passes exact
source-pair run `37441973999` against MolSysMT
`5e2721691b6a3c175406a8e4c0926dfb7b160671` on Python 3.14.7: Linux
**2,819 passed/27 skipped**, macOS **2,792 passed/54 skipped**, Windows
**2,793 passed/53 skipped**, zero failures. All three installed-source builds,
`pip check`, origin/native-resource audits and real integration pass.
The real local Mol*/WebGL2 browser lane also passes **39/39 core suites**,
including 17 Interactions calculation forms. Exact native job identities,
local provider provenance and excluded scope are retained in
[the handoff receipt](source_pair_handoff_20261006.json).

These fixed identities preserve the earlier handoff. The subsequent #168
query-vocabulary integration uses a newer exact provider commit and needs its
own completed native/browser/notebook evidence before the next coordinated
staging preparation. Source handoff precedes compatible package qualification
and does not depend on a provider release arriving first. The separate public
CI/core-browser runs still fail with the old provider. No tag or 1.0 clearance
is created.

**CI environment repair (2026-10-06): #161/#162/#163 resolved in source.**
RDKit is now declared in both scientific test environments and the local
development recipe. The guard rejects its removal from each of the three
recipes; the distribution module passes 19 tests and the real Interactions
family module passes 30. The earlier Python 3.14 source-pair qualification used MolSysMT commit
`5e2721691b6a3c175406a8e4c0926dfb7b160671`, with its own runtime floors,
Node 22 and immediate `pip check`. Public dependency floors are unchanged.
See [the resolved bug record](archive/scientific_test_environments_missing_rdkit.md)
and [the source-pair baseline](pending_proposals/extend_python_support_to_3_14.md#current-scientific-source-pair-baseline--2026-10-06).

The once-run complete regression returns **2,820 passed, 23 skipped and one
failed guard**, in 556.22 s. #162 identifies a profiler that counted SMonitor's
shared wrapper as full serialization. It is corrected with an unwrapped target
and a real serialization positive control; its 22-case scene module passes.
The complete suite was not repeated. Preserve this distinction in
[the receipt](ci_environment_repair_20261006.json); the later hosted full-suite
confirmation above supplies the clean source verdict.

The first hosted source-pair run `37438220076` installs the pair on all three
native platforms and collects its scientific cases without the RDKit defect.
All three full suites expose an OpenMM omission for complementary AMBER
files (#163) and a link to the untracked local design mockup (#114). The
follow-up declares OpenMM in test/development recipes and links the tracked
Studio design record, preserving the scratch artifacts. A clean-checkout
reference guard now rejects existing untracked targets. The 47-case local
AMBER/distribution/link selection passes; exact hosted confirmation above
closes [#163](archive/amber_test_environments_missing_openmm.md). The public
core lane still fails on absent `molsysmt.h5msm`, and the
experimental Qt lane fails to create WebGL; neither is the repaired RDKit defect.
Exact job counts, diagnostics and the bounded follow-up are in
[the hosted record](ci_hosted_followup_20261006.json).

The preceding audit identified three separate hosted causes: missing RDKit
during Python collection; published MolSysMT 0.22.4 missing Interactions/H5MSM
in core-browser and notebook consumers; and the stale Whole mask notebook
example (#160), deferred to the final public documentation block. Fixing the
first cause does not close the other two. Source-level provider #312/#313 and
mixed-SDF qualification are complete; compatible published-provider and exact
installed/hosted candidate qualification are the current release blockers.

**Scientific usability corrections (2026-10-04): #158/#159 resolved in source.**
The real widget review found missing query activation and display selections
silently limiting scientific calculation. Studio now activates successful
correlated queries through the public selection owner and offers separate
all/A/between calculation scopes. Real Mol* browser guards verify 20 calculated
observations with one displayed, explicit restrictions and all 17 scientific
forms; the final lane passes in 155.557 s. The once-run complete source regression
passes **2,812 tests, 23 skipped**, in 606.81 s, in `molsyssuite@uibcdf_3.14`;
Ruff, TypeScript and official runtime rebuild pass.

MolSysMT #312/#313 are now closed at `577d0ab32`, present locally. Direct
caffeine SDF loading and real 1VII/caffeine batch/progressive composition pass
(620 atoms), with identical coordinates, source/base-region records, state,
region undo/redo and MSV sessions. The five-case identity-prevalidation guard
passes after correcting its negative fixture for the provider's new missing-parent
semantics; a dated correction is appended to #157's archive. No provider edits
are made here. See [the follow-up](scientific_usability_review_20261004.md) and
[its receipt](scientific_usability_review_20261004.json).

**Next:** qualify a compatible published provider and the exact installed/hosted
candidate. #151's source-level provider blockers are removed; its existing
published-artifact qualification remains partial. Public documentation follows
functional closure. The 0.24.0 recommendation stands; no tag or installed/hosted
certification is created by these source results. Earlier dated observations
retain their own inputs and are superseded by this handoff where indicated.

The source commit is `c598d2f2`, pushed without a skip marker. Its initial
hosted policy check exposed formatting debt: 88 files are normalized with pinned
Ruff 0.16.5 and identical before/after ASTs, preserving functional evidence.
The hosted notebook lane also exposes the published-provider block and the stale
Whole mask example now tracked as #160 for the final documentation block.
See the follow-up above and `format_policy_followup_20261004.json` for the
distinction between functional qualification and remaining hosted evidence.

**Candidate identity correction (2026-10-04): #157 resolved in source.**
Initial, replacement and composite loads validate public atom identities on the
detached candidate before committing it. Five targeted guards pass, including
malformed native input and real progressive/batch protein–caffeine refusal.
The prior system, coordinates, scene objects, source maps, analyses and undo/redo
remain intact, and its session still round-trips. The once-run complete source
regression passes **2,808 tests, 23 skipped**, in `molsyssuite@uibcdf_3.14`;
Ruff and diff checks pass. See [the resolved record](archive/mixed_partial_hierarchy_load_breaks_scene_state.md)
and [the scientific review receipt](scientific_use_review_20261004.json).

**Next at that checkpoint:** obtain the public MolSysMT fixes for #312/#313, then qualify successful
mixed-source loading. Safe refusal resolves the consumer preparation defect;
it does not establish feature availability. MolSysMT's unrelated local work is
preserved. No version tag or new installed/hosted certification is claimed.

**Scientific-use review (2026-10-04): bounded workflows pass; mixed SDF remains open.**
The reviewed source and devguide reconciliation are pushed at `0dea171d` and
`cdbf52b3`. Four real PDBs (7,953 atoms) agree between batch/progressive loading;
source visibility, isolation and session restoration pass. Real pentalanine,
periodic images/Å, solvated villin and 2HGR candidate calculations pass, along
with public Interactions save/import/repeated extraction and offline HTML
readiness in actual Chromium/WebGL2. The scientific review found SDF count
dispatch failure (uibcdf/molsysmt#312) and mixed missing-group getter failure
(uibcdf/molsysmt#313). The latter also exposes a Viewer candidate-prevalidation
gap (#157): loading can accept a scene that later cannot export state/history.
These failures are reproduced and reported, without provider patches or invented
hierarchy. See [the review](scientific_use_review_20261004.md).

That review's preparation finding is corrected in the follow-up above.
**Next:** address the two provider defects, then qualify the repaired
mixed-source workflow. A minor version **0.24.0** is recommended; no tag was
created. Compatible published dependencies, exact-artifact/hosted gates, final
public documentation and human observations remain. Older passing results retain
their original input boundaries.

**Reviewed source integration (2026-10-03): committed and pushed.** Commit
`0dea171db750c289e6b1f85c2407f91f3ce58f4a` integrates the accumulated public
API, Interactions, scene corrections and composite loading. The final once-run
source regression passes **2,805 tests, 23 skipped**, in 510.35 s, explicitly in
`molsyssuite@uibcdf_3.14` (Python 3.14.7). Ruff, TypeScript and the official
runtime rebuild pass. All **715/715** public callables remain digested, with
explicit `skip_digestion=False`; 441 named digesters have no missing entries.
Review additionally corrected repeated-structure Interactions display transfer
(#156), including current-frame, source-map and session guards. The pre-existing
ACKREDIT stash and three sandbox mockups remain preserved.

This was an internal `[skip ci]` integration using the existing deferred route.
GitHub accepted the maintainer's direct push through its branch-rule bypass;
required hosted checks are not certified by that operation. Published MolSysMT
0.22.4 lacks Interactions. Compatible published dependencies, exact installed
artifacts and hosted-candidate checks remain release gates. The prior 39/39
core-browser and installed results below retain their original inputs; the new
transfer fix has source qualification, not a newly built installed-artifact
claim. See [the review](integration_review_20261003.md) and its
[machine-readable receipt](integration_review_20261003.json).

The next steps are developer-guide reconciliation, assessment of a new minor
version, and representative scientific-use review. Do not tag as a development
checkpoint or infer 1.0 readiness from this integration. Public documentation
remains the last functional-closure block.

**Earlier integration completion (2026-10-03, before reviewed commit): local gates pass.** The corrected
source candidate passes **2,800 tests, 23 skipped** in 489.46 s. The prior installed
wheel passes **2,791 tests, 25 skipped** in 579.31 s; that complete installed run
precedes #155. The latest box-verified wheel passes **68 installed loading/cell
cases**, and its real published-provider guard passes separately. All **39 core
browser suites pass under their normal 180-second deadline**, with no skip
opt-out or local deadline override. Lifecycle, scientific geometry and all 17
calculation forms remain mandatory. #154 and #155 are fixed and guarded locally;
their records stay partial until product publication. The newer editable provider
has closed #307/#309: partial H5MSM composition works through all six atom/frame
selection combinations, without a Viewer scientific composer.

The latest artifact is `0.23.4+76.g924da3a3.dirty`, SHA-256
`24f9adf4235d4d57250d508e48d172f1f4a8c02a1e6fcca1a3c1b4e58251d190`;
614 packaged Python sources match the product tree and runtime-version validation
passes. The experimental installed provider remains `0.22.4+122.g396e6979f`.
Published MolSysMT 0.22.4 still cannot initialize the cell in this route and lacks
Interactions; the safe-error guard is not feature availability. A compatible
published provider, reviewed product commit and exact-source installed/hosted
matrix remain before publication. No product commit or push has occurred.
Standalone/remote scopes and explicit skips retain their limits. Evidence and
artifact distinctions: [`integration_completion_20261003.json`](integration_completion_20261003.json).

**Studio loading slice of #151 (2026-10-03): implemented locally and verified.**
System now offers explicit independent/complementary inputs, add/replace/append,
labels, atom/frame selectors and ordinal pairing. The empty-view welcome action
opens it. Paths must be available to Python; no browser-upload transport is
introduced. Exported browser-only views omit the form. The public load owner
performs scientific preparation; matching runtime acknowledgments preserve the
draft and permit retry. Studio stays open during a pending system rebuild.

All 18 new Python guards pass. The once-run complete Python regression passes:
2,783 passed, 23 skipped in 470.79 s, outside the sandbox in
`molsyssuite@uibcdf_3.14`. JS passes 320 cases; final affected Studio modules pass
39 after the visibility correction. TypeScript and runtime builds pass. The
extended real-Mol* composite suite verifies mixed loading, retry, progressive
addition, replacement, complementary Amber forms, append and nonconsecutive
multi-frame pairing, alongside session/extraction/source visibility. Actual
acquisition of four PDB IDs gives 3,017 atoms/four sources/four regions; adding
a native demo gives 3,039 atoms/five sources/five regions.

The original partial-H5MSM extraction failure is preserved in
[`studio_loading_20261003.json`](studio_loading_20261003.json). The newer editable
provider repairs both extraction (uibcdf/molsysmt#307) and composition
(uibcdf/molsysmt#309). Current positive and older installed refusal semantics,
full regression outcomes and artifact boundaries are in the latest integration
completion above. #151 remains partial for publication and exact-candidate gates.

The earlier #151 slices are implemented locally: [whole-only base-region
visibility](region_visibility_20261003.json), [persistent isolation](region_isolation_20261003.json),
[explicit composite loading](composite_loading_20261003.json),
[durable source transfer](source_records_20261003.json) and
[controlled box assignment](box_assignment_20261003.json). Their scoped guards,
renderer observations, compact-map benchmark and dated regression boundaries
remain in those records. The source-transfer full attempt was interrupted by
ENOSPC; the controlled-box attempt completed with one corrected inventory guard.
The later complete Studio regression above passes on the recovered temporary
filesystem. Each older record retains its original outcome and boundaries.

**Integration follow-up (2026-10-03): local qualification in progress.**
Development now uses the principal maintainer's required
`molsyssuite@uibcdf_3.14` environment explicitly (Python 3.14.7). Viewer and
MolSysMT import from their local checkouts. Provider HEAD is
`bd65456e0ca994f4a92800bda5d23325c999a673`; its unrelated local work is preserved.
Thirteen design guards and 179 affected Python cases pass there (three explicit
environment-dependent skips). All 17 real Interactions calculation forms pass
in Chrome outside the executor sandbox. The complete core lane was interrupted
at the principal maintainer's request to pause for the #151 design discussion:
19 suites passed and Interactions was in progress. It used the existing local
600-second budget, justified by the measured six-minute forms workload; neither
a complete core pass nor the default 180-second budget is certified here.

The earlier integrated Viewer wheel is `0.23.4+71.g3b475639.dirty`; all 608 packaged
Python sources matched the working tree at that qualification. It does not
contain the later region-visibility changes. Its runtime version validator
passes. The same wheel passes 13 design guards and 114 ordinary public workflow
cases with published dependencies; the experimental installed pair passes
23 design/Interactions cases, 68 collection corrections and four CLI guards.
The once-run full installed regression failed (2,583 passed, 15 failed,
44 errors, 25 skipped). Disk exhaustion, qualification-copy omissions and a
native CLI crash are retained in the evidence; scoped recovery is not a passing
full run. The fixture namespace defect #153 is fixed locally with an installed
subprocess guard. Source browser bridges do not establish strict wheel-only
qualification. See [the integration record](integration_qualification_20261003.json)
and [artifact follow-up](installed_artifact_qualification.md#integrated-design-candidate--2026-10-03).
No product commit or push has occurred. Compatible published-provider and
exact committed-candidate gates remain open.

**Multi-source completion remains open:** the authorized loading slice is above.
Loading, source transfer, controlled box assignment and Studio parity are
implemented with qualification limits above; integrated/artifact evidence and
compatible published-provider boundary remain before #151 closure.

**Final design corrections (2026-10-03): implemented locally; candidate
qualification pending.** #146–#150 cover coordinate annotation lifecycle and
rendering, system identity/cache correctness, validation before replacement,
Style ownership and numeric trajectory plot axes. The new #151 records the
principal maintainer's required discussion of batch/progressive loading of
multiple PDBs, PDB IDs or compatible forms. Settle its minimum before freezing
the API. Follow [the current design closure order](final_design_closure_20261003.md).
Public documentation remains last; existing provider/artifact gates still apply.

**Evidence for this block:** 13 new design guards pass; the scoped identity and
scientific correction selection passes 90 cases; reporting/public API checks
pass 198. The single complete Python attempt returned 2,598 passed, 38 failed
and 26 skipped. All 38 failures were the missing-hierarchy identity regression
and pass after its correction; no second complete attempt or final candidate
pass is claimed. The complete JS attempt passed 313 cases; final changed
annotation/trajectory/plot cases pass an 18-case selection outside the sandbox.
Real Mol* Annotations, Studio Annotations and numeric trajectory plot browser
suites pass. Runtime/harness builds, TypeScript and reviewed-source Ruff pass.
All 713 public callables retain digestion and explicit bypasses. The 42 queued
records agree with GitHub. Exact counts, commands/artifacts, source hashes and
remaining integration gates are in
[the retained evidence](final_design_closure_20261003.json).

**Public workflow completion (2026-10-02): implemented and locally verified.**
Four authorized items are now in the working tree: bounded public Interactions
pages independent of rendering (#142), retained multi-card trajectory plots
with state/session/transfer and structure-axis validation (#143), native complete
named-analysis H5MSM save (#144), and per-observation selection/focus in Python
and Studio (#145). Their reports remain partial pending product integration and
supported-candidate qualification. Scientific save preserves sparse coverage,
parallel/grouped observations, units and periodic images. Observation actions
reject stale identities before changing selection/camera. Focus uses canonical
system coordinates. Plot hide/close retains data, clear removes it, and known
extraction maps values/x/events even for repeated or nonconsecutive frames.

**Validation of this source snapshot:** 87 initial focused cases passed; the
single full Python attempt returned 2,576 passed, 20 failed and 26 skipped.
All 20 failures involve sandbox socket/browser restrictions; the five affected
modules subsequently passed outside the sandbox (53 passed, one explicit GPU
skip). A later public API/new-regression selection passed 236 cases; the final
plot/load/edit integration selection passed 38. No second full run or green
final-candidate suite is claimed. JavaScript's complete attempt returned 309
passed, three failed; two obsolete hide expectations and the missing close-event
manifest declaration were corrected and their six scoped checks pass. Runtime
and harness builds, TypeScript and the reviewed-file Ruff check pass. Real
Mol* trajectory-card and complete Interactions subpanel browser suites pass,
including the new row actions, 20 family scenes and 17 calculation forms.
The public inventory has 713 digested callables, explicit bypasses and 437
argument digesters, with no omissions. Evidence and source hashes:
[public workflow record](public_workflow_completion_20261002.json).

**Earlier provider qualification (2026-10-02):** clean experimental MolSysMT commit
`396e6979f3f686b110431f18bba0d41933ce71e2` was installed in the then-used
environment (Python 3.14.7, Pandas 3.0.6, NumPy 2.4.6). This is source Viewer
validation, separate from the earlier installed-wheel qualification using
NumPy 2.5.3. Provider issues uibcdf/molsysmt#288 and #289 remain verified and
closed; earlier installed checks and preserved failure/correction records live
in [the installed follow-up](installed_artifact_qualification.md#provider-invalidation-guards-and-installed-follow-up--2026-10-02)
and [the invalidation record](interactions_invalidation_20261002.json).
Published MolSysMT 0.22.4 still lacks the required Interactions APIs. #114/#140
remain partial for compatible published dependencies, a committed candidate and
exact-candidate installed/core CI evidence. Headless browser correctness does
not qualify GPU throughput or all native platforms. Scientific save's hard-link
publication still needs native filesystem qualification.

**Next:** finish the supported-provider/publication boundary, integrate the
preserved product work through reviewed commits/direct main pushes, reconcile
public documentation last, and run exact-candidate release gates plus the agreed
final human/design review. No product commit, push or release occurred in this
block. Preexisting work is backed up and preserved; local/remote main were at
`f2b148722e32e2f83bc690e51e6aa622b2e31294` at the last synchronization.


**Interactions family API (2026-10-01, local product working tree):** #140
adapts the nine implemented experimental MolSysMT families through explicit
namespaces (`view.interactions.hbonds.get_hbonds`, etc.). Every getter has a
closed signature, ArgDigest and `skip_digestion`; shared calculation coordination
is private. Scientific analyses are named/stored independently from
`view.interactions.add()` visual sets. Both water orders, compound charge/ring
centroid guides, halogen roles and metal candidates are supported without
discarding scientific participants. Occurrences and drawn segments are counted
separately. Evidence-label interning is canonicalized for H5MSM signatures.
The calculation API is now family-only: both old manager-level `compute_*`
methods have been removed and all executable consumers migrated, including the
scientific tools and notebook. That cleanup passes 77 focused tests; the public
inventory now counts 709 digested callables with explicit bypasses and no missing
argument digesters. The public-provider compatibility probe also passes.
**Studio controls (2026-10-02):** calculation now uses criterion selectors,
quantities with units, angular intervals, ring geometry and water order instead
of a parameter JSON editor. Scientific drafts have stable context identifiers
for focus restoration. The Python angular-interval boundary now builds the
single vector quantity required by the provider. The 16 new control tests and
the once-run JavaScript suite (312 passed) precede the focus fix; browser checks
then verified all 17 real form calculations across scoped correction runs.
The initial browser invocation exposed those defects; scoped corrections
verified the remaining cases. The subsequent complete Interactions E2E now
passes as recorded in the current checkpoint above.
The isolated provider wheel at commit `df1a298e70a419a8f04562f8fb9ffaa92abb3be1`
passes 30 focused Python checks and that block's full Python suite:
**2,533 passed, 23 skipped, zero failures** (322.31 seconds), run once outside the
sandbox after the vector fix. JUnit records are
`/tmp/msv-interactions-controls-python-full.xml` and
`/tmp/msv-interactions-controls-python-targeted.xml`. Skipped external/GPU cases
retain their qualification limits. Runtime/harness builds and Ruff pass.
The expanded real Mol* Interactions suite passes, including 20 new calculated
and restored scenes. #140 remains partial: code is uncommitted, compatible
published-provider and whole-product publication CI remain pending. See
[the current plan](interactions_pre_1_0_plan.md#family-api-update--2026-10-01)
and [the detailed record](archive/align_interactions_with_molsysmt_families.md).
The sibling editable MolSysMT and prior Viewer work have been preserved.

**Direct-main CI qualification (2026-10-01):** `main` and `origin/main` are
at `1cf7826d4c343bb9f517f2244a4f7ca83f909c52`, with executable changes
qualified at `ca6a3cda9eefcbd878775bcced8e21e7cb9bc069`. Main pushes now trigger the
Python 3.14 source-pair lane (#137), while manual frozen-candidate tag checks
remain intact. Actual execution exposed and corrected an obsolete provider
pin (#138) and native Windows inventory separators (#139). The default is the
published MolSysMT 0.22.4 source commit, without relaxing the declared floor.
Focused qualification passes 187 checks for the provider update and 173 for
the path correction. Run `36926313726` passes the installed-source audit on
all three platforms and completes the full suites: Linux **2,297 passed,
17 skipped**; macOS **2,290 passed, 24 skipped**; Windows **2,291 passed,
23 skipped**. Native metadata confirms audit, Rust/resources, native-path
guard, installed-pair integration and full tests actually executed in each
job. Normal CI `36926313560` and core E2E `36926313665` also pass at the same
executable commit. #137, #138 and #139 are closed and archived; the closure
protocol passes 127 tests; reporting in the restored full working tree passes
144. Synchronization preserved all 287 original work paths outside the three
intentionally updated indexes; this checkpoint was then updated. Product
changes remain uncommitted and require separate publication qualification.

**Release-tool publication (2026-10-01):** the independent dependency and
exact-candidate evidence block (#106, #103, #134 and the #133 integration)
reached `main` by direct push at `518728496525cc36c2b42afb92371432b75f1bcf`.
Its clean publication checkout passes **2,284 tests, 15 skipped**, exit 0,
against public MolSysMT 0.22.4, plus 272 focused checks. This is evidence for
that source subset; it excludes the larger uncommitted product changes.
A synchronization of attribution guides arrived during qualification; after
incorporating it, 161 affected reporting/dependency/configuration checks pass.

The preparation exposed and resolved #136: repository inputs on evidence
actions no longer become source checkouts. Its 32-test guard retains rejection
of actual undeclared and duplicate checkouts. All 318 original changed or
untracked paths retain their exact content/deletion after synchronization.
No package release or promotion occurred. The complete scientific/product
publication still needs a compatible public Interactions provider (#114);
the latest GitHub Release inventory continues to identify MolSysMT 0.22.4.

**Ecosystem and CI closure (2026-10-01):** `uibcdf/molsysviewer#116` is
verified and closed with actual CI, nightly, PR and protection evidence.
`uibcdf/molsysviewer#110` and its last support boundary, #98, are resolved.
Support libraries and developer tools are adopted for the reviewed boundaries.
Scalar colors retain physical quantities, require compatible units on explicit
physical ranges, and keep bare data unit-free. See
[`units_and_quantities.md`](units_and_quantities.md) and
[`python_ecosystem_policy_adoption.md`](python_ecosystem_policy_adoption.md).

The last complete source attempt returned **2,480 passed, 23 skipped, one
failed**, exit 1. The existing B-factor fixture now supplies units; the final
focused run passes 24 tests. No second complete run or new full-suite pass is
claimed. All 296 native JS tests and the runtime rebuild pass. PR #135 was
updated to `84cbc6bf`, passed CI `36907639608`, core E2E `36907639873`
and all three Python 3.14 cells in `36907639590`, then merged into `main`
at `12faa16b`. The scoped tooling changes are published; the other working-tree
changes are preserved. Local integration checks pass 186 tests. Development
with the principal maintainer continues through commits and direct pushes;
open a PR only when the user requests one, as recorded in root `AGENTS.md`.
Next: published Interactions provider (#114), repaired installed artifacts
(#101), public documentation last, then final-candidate and human evidence.

**Dependency-contract checkpoint (2026-10-01):**
`uibcdf/molsysviewer#106` is resolved in the working tree. The read-only audit
derives runtime constraints and Python bounds from `pyproject.toml`; the route
inventory covers recipe, runtime environments, packaging-only exclusions and
the exact source-pair provider. It runs before packaging, first in the release
gate and in metadata CI. Source-pair CI additionally checks installed provider
version, local origin and clean requested commit before scientific consumers.
This hosted invocation now executes on main pushes: run `36926313726` passes
the installed-source audit on Linux, macOS and Windows. Complete native/source
qualification is tracked in #137, #138 and #139 above.
See [the dependency contract](dependency_contract.md).

All **29 auditor tests** and **62 related packaging/release tests** pass. The
single complete source regression passes **2,464 tests, 23 skipped**, exit 0
in 316.90 seconds, with the isolated MolSysMT export fixed at
`ece35e622fc3f26c57f5261088fa07a39f081aca`. This also verifies the corrected
numeric-template fixture from #107. Log:
`/tmp/msv-dependency-contract-full-python-20261001.log`. Public floors, the
MolSysMT CI source pin and scientific behavior remain unchanged.

The current developer-guide handoff and release plan are reconciled below.
The later ecosystem/CI checkpoint above completes that review. Qualify a frozen
candidate's repaired Conda/Windows artifact (#101), compatible published
Interactions provider (#114), required hosted evidence and human workflows.
Public documentation remains last; no candidate was published here.

**Diagnostic-template checkpoint (2026-10-01):**
`uibcdf/molsysviewer#107` is resolved in the working tree. All 48 catalog codes
have renderable templates; the completeness guard now starts from the entire
catalog. Real emission checks preserve context and render all six repaired
diagnostics in the five SMonitor profiles. The official integration verifier
passes all four checks. Code metadata and recovery behavior are unchanged.

The complete source attempt returned **2,433 passed, 23 skipped, one failure**
(exit 1, 317.91 seconds): the generic template fixture supplied strings for new
numeric format fields. After correcting that fixture to supply actual numeric
types and respect format specifications, both affected modules pass **95 tests,
14 skipped**, exit 0. No second full run was performed; a fresh all-green full
suite is not claimed here. Details and logs are in
[the archived #107 record](archive/emitted_smonitor_codes_lack_templates.md).
The later ecosystem checkpoint resolves #110. The dependency
floor/source-pin audit (#106) is resolved above; qualify a candidate for the repaired
Conda/Windows (#101) and compatible Interactions (#114) gates. Public
documentation remains last.

**Shared public-verifier checkpoint (2026-10-01):**
`uibcdf/molsysviewer#133` is resolved. Existing hosted run `36860171883`
at adoption commit `a8aa669c` successfully calls the pinned common verifier
and uploads independent evidence for the exact public noarch file. GitHub ZIP
digest/run/commit association and the `molsyssuite.public-conda@1` report were
checked. The whole run fails because Windows reproduces #101's missing
`molsysviewer` launcher; that defect remains partial and now reproduced.
No workflow dispatch, package upload or promotion was performed here.

The local branch incorporated ten published main commits by fast-forward with
automatic preservation of tracked work. Archive/generated-index conflicts
were resolved; product/docs tracked bytes match the preserved autostash
`d0a4fb2c`. The candidate/promotion tools now import successfully after removing
their dependency on the deleted local verifier. Existing installed artifact
bindings retain exact builds, MD5 and SHA-256 for both channels, while shared
public verification is called by its owner workflows. #134's gate is preserved.
The final focused slice passes **114 tests**; complete source regression passes
**2,418 tests, 20 skipped**, exit 0 in 295.06 seconds, with the previously
qualified isolated MolSysMT export fixed at `ece35e622fc3f26c57f5261088fa07a39f081aca`.
Log: `/tmp/msv-shared-verifier-full-python-20261001.log`. Public documentation
remains deferred. Diagnostic templates (#107) and the dependency-floor audit
(#106) are resolved above; the next release work requires a frozen candidate
for the repaired Conda/Windows and compatible Interactions gates.

**Promotion-gate checkpoint (2026-10-01):** `uibcdf/molsysviewer#134` is
resolved in the working tree. Promotion shares the current four-platform pair
coverage/scientific-step checks and requires a successful staged Windows
launcher run matching the Viewer commit, version, build and SHA-256. Windows
dispatch must use a branch/tag at the candidate SHA. The operator contract is in
[the release evidence guide](release_gate_evidence.md#exact-file-promotion-and-windows-launchers).
The 103 focused tests passed; the complete source regression passed **2,402
tests, 20 skipped**, exit 0 in 307.36 seconds. To keep the provider fixed during
concurrent MolSysMT work, that run used an isolated export of committed
`ece35e622fc3f26c57f5261088fa07a39f081aca` with its existing native extension.
Exact identities and logs are in the archived #134 record. The final workflow
guard and metadata were checked separately after strengthening its assertions.
No repaired candidate has passed hosted Windows yet, so #101 remains partial.
The current changes still need a frozen candidate before staging/public
certification. Shared public-verifier adoption (#133) is resolved above;
public documentation remains deferred.

**Release-gate checkpoint (2026-10-01):** `uibcdf/molsysviewer#103` is
resolved. The verifier now assesses the exact candidate rather than printing
an unconditional Conda blocker. Staging pair, public pair/channel state and
hosted core E2E are separate checks; each binds versions, builds, commits,
run attempts and the actual installed environment artifacts. ZIP and installed
MD5 identities are tied to GitHub/channel SHA-256 records. Missing evidence
blocks, contradictory evidence fails, and declared pre-1.0 exceptions remain
nonzero rather than becoming passes. Strict 1.0 rejects exceptions. See
[the local evidence contract](release_gate_evidence.md).

Fresh complete regression: **2,370 Python tests passed, 20 skipped**, exit 0
in 311.70 seconds. This closes the interrupted collection evidence gap from
#131 below. The 56 focused release tests and all 18 guard mutations also pass;
mutations restore exact source bytes/timestamps. A real historical public
environment verifies the archive, installed coordinates and live channel
bindings, without certifying the current candidate. MolSysMT remained clean at
`ece35e622fc3f26c57f5261088fa07a39f081aca` before/after; its checkout was not
modified. Log: `/tmp/msv-release-gate-full-python-20261001.log`.

This task changes Python development tools/tests and internal records, with no
TS/runtime product change. Earlier JS/core/performance results remain separate
evidence. The current dirty tree still has no frozen release candidate, and
the missing-candidate CLI correctly reports three blocked evidence steps with
exit 2. Next technical block: the repaired Conda artifact and exact Windows
launcher observation (#101); compatible published Interactions qualification
remains #114. Public documentation is still deferred until functional closure.

**Installed package checkpoint (2026-10-01):** the current local Viewer wheel
passes **182 selected tests** with public MolSysMT 0.22.4 and published support
packages in an isolated Linux/Python 3.14 environment, including eight real
offline Chrome HTML checks. Molecular imports resolve exclusively to installed
site-packages; pip requirements and Python/runtime/wheel versions agree. The
installed provider probe passes ordinary views and explicit refusal of the
unavailable Interactions backend. Exact artifact hashes, versions, commands and
scope are in [the installed qualification record](installed_artifact_qualification.md).
No sibling package or dependency floor was changed; #114 remains partial.

`uibcdf/molsysviewer#131` resolves test helper imports in installed and ordinary
collection modes. The original 89 affected development checks and 59 lifecycle,
teardown and addon checks pass; the latter also pass installed. The required
full development attempt stopped at two bare `conftest` imports during
collection. Those imports and the function-local addon reference were fixed;
complete collection now passes. This is not a new passing full-suite result.
The later 2,370-pass complete regression is recorded above; the preceding
2,330-pass product regression below remains separate evidence.
Public documentation remains last. Next: qualify Interactions when its
compatible provider is published, then reconcile the final support promises
and freeze a candidate for its own complete gates.

**Public HTML checkpoint (2026-10-01):** uibcdf/molsysviewer#128–#130
are resolved. Shared non-inline exports carry a versioned scene sidecar,
readiness follows strict complete restoration and a new Mol* draw, and Studio
receives the current authoritative panel summaries. Actual offline inline and
HTTP shared artifacts preserve regions, annotations, measurements, shapes,
selections and periodic hydrogen-bond geometry across three frames. Invalid
sidecars/restoration reject visibly; Python-owned controls explain their session
requirement without changing the saved scene. Six guard mutations fail and
exact source/runtime are restored. Public documentation remains deferred.

Fresh local evidence: **2,330 Python tests passed, 20 skipped**, exit 0;
**293/293 JS units**, TypeScript checking, regenerated runtime, **36/36 core
browser suites**, and both performance harnesses pass. The artifact suite also
passes after adding explicit format/messages rejection and restoring the schema
guard. Logs are `/tmp/msv-html-full-python-20261001.log`,
`/tmp/msv-html-js-unit-detail-20261001.log`,
`/tmp/msv-html-core-e2e-20261001.log`,
`/tmp/msv-html-final-artifacts-20261001.log` and
`/tmp/msv-html-final-performance-20261001.log`. Tests use canonical Python
3.14.7 and Chrome/SwiftShader, with no browser skip opt-out. Provider HEAD was
observed at `c6e02d930297990cbd0f0023eea5e7e271c31e92`, with independent
ongoing changes preserved. This is development-checkout evidence, not a
published-provider or frozen-candidate qualification. The ordinary installed
package check is now recorded above; compatible scientific-provider artifacts
remain pending. Documentation follows
functional closure. Shared-runtime local-file restrictions remain #39;
standalone is experimental and remotes remain post-1.0.

**Public persistence checkpoint (2026-10-01):** `uibcdf/molsysviewer#127`
guards rejection of invalid session scenes before an existing destination is
replaced. The isolated scene restoration borrows the incoming MolSys rather
than copying the trajectory, and closes its temporary widgets on both success
and failure. A failed newly allocated destination is also closed. The guards
preserve system and handle identity, scene, coordinates, undo/redo and replay;
scientific scene tests cover incompatible signatures, units, filters and
versions. All three guard-removal experiments fail, with exact source bytes
restored afterward. A fresh full Python 3.14 run passes **2,313 tests,
20 skipped, no failures**, exit 0 in 287.11 seconds; log:
`/tmp/msv-session-full-20261001.log`. MolSysMT HEAD remained
`18cc43021a663b5c79b8aa7b51cdef5e1fe27785`, with independent provider changes
preserved. This is development-checkout evidence; published-provider and exact
candidate qualification remain pending. The session format remains
experimental. Public documentation is deferred to the final pass by the user;
the completed HTML follow-up is recorded above.

**Final design review (2026-09-30):** issues `uibcdf/molsysviewer#118`–`#124`
are closed, implemented and guarded. Annotation creation is now only
`view.annotations.add`; `uibcdf/molsysviewer#125` extends the public inventory to
exported class methods and returned scene handles. All 699 reachable ordinary
callable routes have ArgDigest and explicit `skip_digestion=False`, with no
exemptions or missing named digesters. Eight guard mutations fail as intended
and the exact source bytes were restored after each experiment.

**Validation checkpoint after the corrections (2026-09-30):** a fresh complete
Python run including the four real scientific checks passes **2,296 tests,
with 20 skips and no failures**, exit 0 in 274.18 seconds. It used canonical
Python 3.14.7 and PySide6/Qt 6.11.2, outside
the sandbox with its matching `CONDA_PREFIX`. The skips include explicitly
unselected Chromium/GPU checks and unavailable test branches; they are not
certification of those paths. The four scientific checks passed before this
full run; the preceding documentation validation passed 2,292 tests and the
42 selected public-contract/scene/documentation tests. No
`DigestNotDigestedWarning` appears in the full report.

A **clean strict Sphinx build passes without warnings**, exit 0. The six
heading warnings are corrected in `uibcdf/molsysviewer#126`: the historical
design subsections now use H2, and the home notebook has an H1 title and its
four governed anchors. Its existing H2 sections, examples and outputs are
preserved. Sphinx ran in the existing Python 3.13 documentation environment;
the canonical Python 3.14 environment does not have Sphinx installed.

Commands, both from the repository root with the relevant environment active:

```bash
python -m pytest --receptor=llm tests/
sphinx-build -E -a -b html -W --keep-going docs /tmp/msv-validation-20260930-docs
```

Local logs are `/tmp/msv-real-interactions-full-20260930.log` and
`/tmp/msv-validation-20260930-sphinx.log`. This validates the uncommitted
working tree based on `6f49013c80c7a10eb09a1220b2236d879d8ecd5a`, with
MolSysMT imported from its development checkout. It is not a published-provider
or frozen-artifact qualification. Earlier design-review evidence remains:
JS 293/293, TypeScript checking, runtime rebuild, core browser 36/36 and the
message/region performance checks pass. Those complete lanes were not repeated
for the subsequent documentation and qualification-tool changes; the expanded
Interactions browser case passes separately with actual calculated links and
restored-session geometry. The earlier design-review full Python
run had nine failures; they were corrected and checked by affected selections
before this separate validation task. A frozen 1.0 candidate still needs
its own complete gates.

**Interactions scientific checkpoint (2026-09-30):** real sparse queries,
units/PBC geometry, complete and interactions-only H5MSM 0.5 imports and MSV
session restoration pass. A real 5,000-frame detector calculation produced
2,248 occurrences in 3.93 seconds; warm atom/frame queries took about 0.50 ms.
The solvated 4,369-atom workload produced 2,439 observations, including 299
with periodic images. Eight 2HGR sulfur proximity candidates preserve the
existing topology. See [the qualification record](interactions_qualification.md)
for exact workloads, source provenance, tests and limits.

The public channel still offers MolSysMT 0.22.4, which lacks the required
backend. Its real compatibility probe passes for ordinary views and explicit
refusal of calculation. Keep #114 partial/experimental until a compatible
provider is published and the installed-artifact checks pass. The final
four-workload source qualification used clean provider commit
`18cc43021a663b5c79b8aa7b51cdef5e1fe27785`, observed unchanged before/after;
the complete Python run occurred during its independent development work.

**Earlier Interactions working-tree evidence (2026-09-30, before the final review):** Native Interactions now includes
scientific Python workflows, tagged current-frame geometry and the Studio tab.
The review fixes protect domain picking, same-frame inspector replies, deletion
during a Mol* write and occurrence materialization budgets. The full Python
suite in the canonical Python 3.14/Qt 6.11.2 environment passed **2,235 tests**
with **20 skips**, outside the sandbox and with its matching `CONDA_PREFIX`.
JS units passed **294/294**, and the core browser lane passed **35/35** after
the Interactions addition. This supersedes earlier local full-suite failure
observations below; it does not certify a visible-window standalone host.

The requested final library-design review produced issues #118–#125, recorded above.
Interactions remains experimental under `uibcdf/molsysviewer#114` until its
published scientific backend and exact candidate are qualified. Six synthetic
combined-memory workloads are recorded in [interactions_performance.md](interactions_performance.md).
The bounded paging fallback names `uibcdf/molsysmt#264`; unrelated Sphinx public
reference warnings and cold imports were corrected in `uibcdf/molsysviewer#117`;
the final Sphinx build passes with warnings treated as errors.

The public MolSysMT 0.22.4 / MolSysViewer 0.23.4 pair is installed and
verified across Python 3.11–3.14. It is a pre-1.0 distribution
baseline, not an exact 1.0 candidate. Future native Conda candidates
exclude macOS Intel; the four supported platforms and final release
gates need fresh candidate evidence.

On Linux, the shared `molsyssuite@uibcdf_3.14` development environment
now uses official conda-forge PySide6/Qt 6.11.2. Qt-host and
MolSysMT–Viewer targeted tests pass. The UIBCDF family remains a
separate fallback, not a dependency of that environment.
Visible-window Qt and native macOS/Windows standalone validation
remain unproven. The earlier full Viewer suite was not green: three
test-environment/assertion failures were corrected and their affected
files passed, but the complete suite was not rerun.
On 2026-09-28 another full local run, launched from the older shared Python
3.13 environment, reached 83% before a native crash while importing
`PySide6.QtWebEngineCore`. That prefix mixes conda-forge Qt/PySide 6.9.3
with UIBCDF WebEngine/Qt 6.9.2 packages. It is not a green suite or a
product regression verdict; the #99, #101 and reporting-protocol selections
passed separately. The canonical 6.11.2 environment remains the relevant Qt
development baseline.
On 2026-09-28 a complete Viewer suite in that canonical Python 3.14
environment reached 100% with two Qt subprocess failures under this executor's
sandbox: Chromium aborted in `sandbox_host_linux.cc` with `Operation not
permitted`. Both exact Qt tests passed when rerun outside the sandbox with
`CONDA_PREFIX` set to the Python 3.14 environment. This is not a green
full-suite run or visible-window host certification.

The final design review is implemented. The next checkpoint is published-provider
qualification, exact-candidate gates, scientific dogfooding and first-contact
onboarding. Executable documentation coverage still has growth work; the new
Interactions tutorial runs. The local standalone host and launchers are
experimental for 1.0: visible-window Qt observations and the newer
conda-forge Qt comparison (`uibcdf/molsysviewer#113`) remain host follow-ups,
not candidate-freeze conditions. Run exact-candidate core 1.0 gates before
tagging.
The strict E2E scope is the hosted core non-remote lane; remote-session
certification is post-1.0 (`uibcdf/molsysviewer#100`).
Follow [the ordered actions below](#what-is-next), not the historical
candidate sequence in this file.

## Repository state

- On 2026-09-27 the shared Linux `molsyssuite@uibcdf_3.14` development
  environment switched from the five UIBCDF Qt/PySide 6.10.1 packages to
  official conda-forge 6.11.2. A fresh prefix created from the central
  MolSysSuite YAML and the migrated shared prefix both passed Viewer
  standalone/transport and MolSysMT–Viewer integration selections; the shared
  prefix also passed Xvfb window and SwiftShader render smokes. The recipe
  now includes `python-build` and `imageio`, and a stale macOS runner assertion
  was corrected. One full Viewer-suite run before those fixes yielded 2,132
  passed, 17 skipped, three failed; the affected files passed afterward,
  but the full suite was not repeated. Do not count this as a green full-suite
  or native macOS/Windows gate (`uibcdf/molsyssuite#52`, `#109`).

- On 2026-09-27 the standalone Qt host began migration to canonical
  PySide6/Qt 6.11.2, retaining the UIBCDF family as a fallback. Clean Linux
  Conda probes for Python 3.11–3.14 passed real WebEngine transport and
  two-generation payload delivery before the source change; targeted host
  selection tests pass after it. Windows and macOS ARM currently have solver
  evidence only. macOS Intel is now outside the supported matrix by the
  decision tracked in `uibcdf/molsyssuite#59`; previous Intel package evidence
  remains historical, not a current release gate. `#97` owns the local support contract,
  `#109` owns the Viewer migration, and `uibcdf/molsyssuite#57` remains open
  for suite-wide observation before any fork retirement.
  A manually dispatched [CI run
  36338541516](https://github.com/uibcdf/molsysviewer/actions/runs/36338541516)
  passed 7/7 at `19dadc1a0adb1ff7477fe9e7866e807b015c8f36`, including
  the Linux Xvfb Qt pipeline on canonical 6.11.2. It does not certify a
  visible-window render or a native Windows/macOS Qt host.

- Branch: `main` contains the tagged 0.23.4 release candidate and its
  post-tag fixes; the immutable 0.23.4 tag is
  `cf427942d0b08a1c5c60f262c6a6b33f248d6f8b`. The coordinated
  MolSysMT 0.22.4 / Viewer 0.23.4 pair passed both staging and public
  20-cell installed-package matrices on 2026-09-25. This is a pre-1.0
  distribution milestone, not closure of the [1.0 release plan](path_to_1_0.md).
- On 2026-09-26 the maintainers moved remote-session support and its three E2E
  scenarios to post-1.0. The already distributed code remains an unsupported
  preview; the 1.0 gate now requires the 34-scenario core browser lane, not
  remote-client or server-GPU certification (`uibcdf/molsysviewer#100`). A core
  pass must not be reported as a full 37/37 or a remote pass. The new core
  lane passed locally 34/34 on Chrome 149 with WebGL2/SwiftShader and then
  [passed on hosted Chrome](https://github.com/uibcdf/molsysviewer/actions/runs/36232475620)
  at exact commit `6b519db0f771f5edbff3e21fb0cae203a38da036` (34/34,
  2026-09-26). The first two hosted attempts reached case 34 but exposed
  asynchronous movie-camera races: `stop_movie` returned before queued writes
  settled, and `movie_playback_done` preceded the final camera write. Both are
  now guarded by `js/tests/unit/movie-handler.test.ts` and
  `js/tests/e2e/movie-playback.e2e.ts`; 294 JS unit tests and the targeted
  browser case passed locally before the hosted rerun. `CI_e2e` can also be manually
  dispatched in a separate remote-portable diagnostic mode; that mode is not
  part of the automatic 1.0 gate.
- The previously broken hosted routes now pass against public MolSysMT on
  `main`: [CI run 36233310412](https://github.com/uibcdf/molsysviewer/actions/runs/36233310412)
  passed 7/7 (six Python cells plus the Xvfb Qt pipeline), and
  [notebook run 36233310586](https://github.com/uibcdf/molsysviewer/actions/runs/36233310586)
  passed at exact commit `2bcc86b7903ff91fd78d371a91ab56ff5ec25f78`.
  Together with the hosted core E2E above, these resolve #88; they do not
  replace the visible-window Qt observation or final 1.0-candidate reruns.
- Phases 5, 6, 8 and 9 and the Phase 10 persistence slice were independently
  audited and closed on 2026-08-09. Phase 8 evidence remains in
  [`performance/representative_scale_gate_2026_08.md`](performance/representative_scale_gate_2026_08.md).
- **Gate 9 of Phase 10 is done** (2026-08-12): every public callable is digested or
  deliberately exempt, and every argument name they introduce has a digester. Phase 10 is
  4 of 11.
- Phase 7 stays `⚠ 90%`: its automated seams are complete and its two visible-window Qt
  observations are not, and cannot be done here. Phase 7's Qt remainder is
  outside the core 1.0 gate under the experimental standalone scope decision.
- `sandbox/Smoke_Test.ipynb` is developer-owned scratch state. Never stage it and
  never use it as architectural evidence.
- `molsysviewer/viewer.js` was regenerated with `npm run build:runtime`; it is a
  generated artifact, never a source file.
- **Reports are coordinated with the issue board** (2026-08-14). Documents in
  `pending_bugs/` and `pending_proposals/` carry front matter and a GitHub issue; the
  queue READMEs are generated; `devtools/release_gate.py` is gate 11's command. See
  [`reporting_protocol.md`](reporting_protocol.md).
- `python devtools/devguide_issue.py sync --check` needs the network to compare
  the issue board with front matter. Run it before a release and after closing
  or restatusing an entry. `python devtools/devguide_index.py --check` is an
  offline queue-index check and runs in the local suite.
- The shared reporting vocabulary question raised at
  [uibcdf/molsysmt#156](https://github.com/uibcdf/molsysmt/issues/156)
  is closed; consult the current MolSysSuite reporting policy rather than
  treating it as a pending decision.
- **Citation and Zenodo metadata are a checked contract** (2026-08-14).
  [`release_and_citation.md`](release_and_citation.md) is normative;
  `devtools/validate_citation.py` holds `CITATION.cff`, `.zenodo.json` and the five
  derived surfaces to one concept DOI, and is a step of the release gate.
  `prepare_release.py` updates them in one pass and `verify_zenodo_release.py` checks the
  archive afterwards, because a pushed tag does not request ingestion and the version DOI
  arrives asynchronously.
- **The MolSysMT alias seam is public and closed** (2026-08-14). MolSysViewer commit
  `5bb01b8e` builds its caller-scoped ArgDigest tables from
  `molsysmt.attribute.get_argument_aliases()` introduced by MolSysMT commit
  `4267d414f`; no normalization module imports MolSysMT private alias data. The
  `molsysmt>=0.22.0` floor is the schema boundary, and the durable rule is in
  [`digestion_and_dependencies.md`](digestion_and_dependencies.md). MolSysMT issue
  [#157](https://github.com/uibcdf/molsysmt/issues/157) is closed.
- **The ArgDigest alias-collision blocker is fixed on source `main`** (2026-08-14).
  Commit `c46cd01` rejects alias-plus-canonical and multi-alias target collisions with
  `ArgumentConsistencyError` before normalization can discard a value. MolSysViewer has
  a public regression and raises its wheel and Conda floor to the planned patch release
  `argdigest>=0.12.1`; publication of that release remains a prerequisite for clean
  installation dogfooding.

## Published pre-1.0 pair — 2026-09-25

Viewer [0.23.4](https://github.com/uibcdf/molsysviewer/releases/tag/0.23.4)
and MolSysMT [0.22.4](https://github.com/uibcdf/molsysmt/releases/tag/0.22.4)
are published GitHub Releases on their exact tested candidate commits. The
Viewer ordinary Python wheel and source `viewer.js` were checked against the
0.23.4 runtime before tagging; [#102](https://github.com/uibcdf/molsysviewer/issues/102)
records that guard. The npm runtime 0.23.4 is published and its CDN bundle
returns HTTP 200. A redundant second npm publish triggered by the GitHub
Release was corrected on `main` and archived under
[#104](https://github.com/uibcdf/molsysviewer/issues/104); it did not alter
the successful tag-push publication.

MolSysMT's [public-channel matrix](https://github.com/uibcdf/molsysmt/actions/runs/36129993869)
passed 20/20 clean installations on five platforms and Python 3.11–3.14,
with exact build-3/build-5 coordinates and public `uibcdf` provenance. The
prior staging matrix also passed 20/20 in run `36121427459`. All six exact
Conda files are public with the verified SHA-256 digests. The promotion
actions and receipt uploads passed, but their final duplicated verifier
steps exited 1 after printing the correct public URLs; the workflows remain
red and the defect is tracked by [#105](https://github.com/uibcdf/molsysviewer/issues/105),
`uibcdf/molsysmt#246` and `uibcdf/molsyssuite#48`. Do not rerun mutation
just to change a badge. Replacement read-only verification passed on GitHub
in [Viewer run 36227243079](https://github.com/uibcdf/molsysviewer/actions/runs/36227243079)
and [MolSysMT run 36227235698](https://github.com/uibcdf/molsysmt/actions/runs/36227235698).
The original shell exit mechanism is still unknown; its historical run
conclusions do not change.

The release explicitly excepts visible-window Qt and complete hosted E2E
evidence for this pre-1.0 version; [#100](https://github.com/uibcdf/molsysviewer/issues/100)
remains open and the strict 1.0 gate is not green. The stale unconditional
Conda gate message was tracked by [#103](https://github.com/uibcdf/molsysviewer/issues/103)
and is now replaced by the exact-candidate checks above, without changing the
tested tag. Both public Zenodo
records have now been independently verified. Viewer 0.23.4 has
[version DOI 10.5281/zenodo.22959304](https://doi.org/10.5281/zenodo.22959304)
in concept family `10.5281/zenodo.18072956`, with the single archived file
`uibcdf/molsysviewer-0.23.4.zip` (23,694,420 bytes,
`md5:2cfe76a5ea9ec2894964926db81c2609`). MolSysMT 0.22.4 has
[version DOI 10.5281/zenodo.22959294](https://doi.org/10.5281/zenodo.22959294)
and the source archive `uibcdf/molsysmt-0.22.4.zip`. The initial 900-second
verifiers timed out before ingestion; MT's stricter tree-tag predicate also
caused a false red and was corrected in `uibcdf/molsysmt#247`. Neither
Zenodo inventory contains the separately published Conda/npm packages.
Read-only verification reruns passed on 2026-09-26:
[MolSysMT run 36220716162](https://github.com/uibcdf/molsysmt/actions/runs/36220716162)
and [Viewer run 36220722008](https://github.com/uibcdf/molsysviewer/actions/runs/36220722008)
each reported its exact version DOI. The immutable tags were not moved.

The older 0.22.0/0.23.1 and branch-candidate sections below are dated
history, not the latest release coordinates.

## Historical 0.22.0/0.23.1 coordination — superseded by the public pair

This section records the earlier dependency-cycle diagnosis. It is not a
current instruction to stage or publish those old coordinates; the
0.22.4/0.23.4 pair above supersedes that release plan.

MolSysViewer must keep `molsysmt>=0.22.0`: that is the first MolSysMT line providing
`molsysmt.attribute.get_argument_aliases()`, which MolSysViewer imports without a
fallback. Lowering the floor would make the environment solve and the package fail at
import time.

That boundary was remeasured on 2026-09-19:

- MolSysMT workflow run `33849332945`, commit
  `e5820d4794f8ce31a1f64e345c5edf9073ade975`, published build-2 ABI3 artefacts for
  `linux-64`, `linux-aarch64`, `osx-64`, `osx-arm64` and `win-64` to
  `uibcdf/label/staging`. Each supports Python 3.11--3.13.
- The public channel still stops at MolSysMT 0.12.0 and MolSysViewer 0.7.0. A Linux
  dry-run with staged MolSysMT 0.22.0 resolves on Python 3.12 but not 3.13: MolSysMT is a
  hard dependency of MolSysViewer, and its own runtime dependency on MolSysViewer can find
  only the old interpreter-specific public artefacts. This is the publication cycle,
  reproduced rather than inferred.
- The `0.22.0` and `0.23.0` MolSysViewer tags predate the fixes for
  uibcdf/molsysviewer#88 and #89. They must not be moved, and rebuilding either tag would
  omit the fixes that make hosted CI and the package build reach the dependency boundary.
  Freeze a new candidate version from a reviewed commit before dispatch; `0.23.1` is the
  natural patch candidate, but it is not declared until that release decision is made.
- The MolSysViewer Conda core remains `noarch: python`, bounded to
  `python>=3.11,<3.14`. One package therefore serves the entire supported matrix.

The repository now carries the two missing pre-publication routes:

1. A manual Conda dispatch requires an exact SHA, a new version and a build number. It
   builds the noarch package against `uibcdf/label/staging`, runs the full recipe test,
   and uploads only to the `staging` label. There is deliberately no `--no-test`
   exception: conda-build places the just-built MolSysViewer package in its test channel,
   closing the dependency loop with staged MolSysMT.
2. Manual dispatches of `CI`, `CI_e2e` and `Documentation notebooks` may explicitly
   put staging first and pin MolSysMT 0.22.0. Normal push, pull-request and scheduled runs
   continue to use the public channel. Staging is a release-candidate input, never a
   silent development default.
3. Staging uses Conda build 0 and a GitHub Release uses build 1. Validated coordinates are
   not overwritten with different bytes.
4. Structural guards require the exact checkout, separate staging/main publication
   branches, retained producer evidence, the recipe test on both branches, and the
   explicit staging input on every hosted gate.

The 2026-09-24 state is: MolSysMT 0.22.0 ABI3 build 5 and MolSysViewer
0.23.1 noarch build 1 are in staging. MolSysMT run `35967239820` passed the
exact-pair matrix on five native platforms and Python 3.11–3.13 (15 cells).
That run predated the later explicit Conda-record channel/URL/hash guard and
does not satisfy that stronger check retroactively.

The next hosted Viewer gates have now crossed the original dependency barrier:
documentation run `35997846329` installed successfully, then exposed two
Showcase API/example failures. The pocket-blob Python multi-iso gap is tracked
as uibcdf/molsysviewer#99; the channel example used an obsolete argument.
Both notebooks execute locally after branch fixes, and the hosted
Documentation notebooks rerun `36016496850` passed every notebook on exact
branch commit `7c4e0cd968e9530033e35221683ca085fe1d37cd`. This closes
the staged-dependency documentation execution gap for that candidate, not
the ordinary public-channel `main` gate.
E2E runs `35998036249` and `36016496630` installed and built, then stalled
extracting an unused Playwright Chromium archive; neither entered the browser
tests. The latter stopped at a deliberate 15-minute timeout. The workflow now
checks and records the runner's Chrome, which the E2E harness already selects.
CI run `36017021764` passed the Qt job but failed all six Python matrix jobs
after the solver barrier, exposing missing test-only dependencies and JS setup;
the branch has a local fix and requires a hosted rerun. The staged-dependency
documentation gate is green, but CI and E2E are not yet green.

The follow-up `CI` run `36019810641` then passed Qt and four of six Python
matrix jobs. The remaining cells exposed Node 26 incompatibility in JS
coverage and a macOS fast-close WebSocket test race; the focused corrections
are local only pending another hosted run. `CI_e2e` run `36019810581` reached
22/37 real browser scenarios before a 30-second PNG-download timeout. The
same scenario passed locally, but the local aggregate stopped at 25/37 on
the command-line Chrome/localhost limitation of uibcdf/molsysviewer#77.
Neither environment has certified the full E2E suite; uibcdf/molsysviewer#100
tracks an evidence-lane redesign. Keep the 1.0 release gate open.

The interim split under #100 is now explicit: local source-pair
`test:e2e:portable` passed 36/36 with Chrome 149 and real WebGL2. Hosted
`CI_e2e` has been changed to run that portable lane, but has not yet been
rerun. The excluded `remote-session` is a separately runnable server-GPU
lane, not a skipped pass. `nauta` does have real NVIDIA GPUs outside the
sandbox; its worker still fails to commit command-line HTTP navigation.
Changing the worker to navigate through CDP did not fix it (`Page.navigate`
timed out), so that product change was reverted. The test bridge now reports
stages and has a bounded wait. Defer the GPU launch investigation until after
the coordinated pre-1.0 package publication; no 37/37 or 1.0 gate is claimed.
Staging-enabled `CI` run `36034111547` on Viewer commit `ac3dd891` then
passed Qt but all six Python jobs stopped at one stale distribution guard:
it searched for the former E2E step name rather than the new portable
command. The guard now checks the command itself; 24 focused local tests
pass. The staging-enabled rerun `36036802158` on Viewer commit `2594f1a2`
then passed all seven jobs (six Python matrix cells and Qt). This is branch
CI against the staged dependency, not the public-channel `main` gate.
The portable `CI_e2e` rerun `36038233512` reached scenario 23/36 and failed
at the same hosted PNG-download timeout in `remote-client-rendering` as the
earlier full-suite run. This is not a portable E2E pass and cannot certify
the separately deferred server-GPU lane. Stop rerunning this unchanged test;
the reproducibility/evidence work is tracked by #100.
The detailed diagnosis and later resolution are in
[`archive/hosted_ci_has_never_passed.md`](archive/hosted_ci_has_never_passed.md).

The following was the remaining order at this historical selection checkpoint;
the current state is at the top of this file:

1. resolve or explicitly defer the reproducible hosted
   `remote-client-rendering` PNG-download timeout under #100 before claiming
   a hosted E2E pass; staging-enabled CI passed 7/7 in `36036802158`, but
   the latest ordinary
   CI run `35984241119` could not resolve
   `molsysmt>=0.22.0` from the public channel before reaching product tests.
   The subsequent micromamba `ENOENT` was cleanup fallout, not the cause;
2. repeat the exact-pair gate with the stronger provenance assertion when a
   final release candidate is selected, and settle the clean-install PDB path
   under `uibcdf/molsysmt#200`;
3. decide on public release coordinates and publish only after both projects'
   exact-commit package gates pass, without a bootstrap exception in either
   public build. The deferred server-GPU lane remains visible in #100 and must
   not be represented as a passing hosted or local test.

The then-next candidate decision was recorded: `python-3.14-support` included
the two repositories' `main` revisions at that time, and fresh unoccupied versions
MolSysMT `0.22.4` ABI3 build 0 / MolSysViewer `0.23.4` noarch build 0 are
planned. Anaconda returned HTTP 404 for each version across labels. The
committed route plans require staging; a Release event cannot rebuild a
staged coordinate, and separate workflows promote one exact SHA-256-verified
file at a time after the full 20-cell installed-pair gate. These promotion
workflows have local structural and shell-syntax tests but no hosted promotion
yet. The earlier Viewer CI 7/7 pinned staged MolSysMT `0.22.0`; manual CI,
E2E and notebook gates now require an explicit MolSysMT version input and
must be rerun for `0.22.4` rather than credited retroactively. At this
selection checkpoint, neither package had been uploaded; build-0 staging is
recorded below. #100 still owns the hosted E2E
timeout and the separate server-GPU lane.

The maintainers accepted an explicit, limited pre-1.0 exception for this
`0.22.4`/`0.23.4` candidate: the hosted portable E2E failure in
`36038233512` and the unvalidated server-GPU lane do not block *this package
publication* if all other exact-candidate gates pass. Local portable E2E
passed 36/36, but hosted portable E2E did not pass and full 37/37 has no
certification. #100 remains open; the strict 1.0 E2E and visible-window gates
were unchanged for the 0.23.4 decision. The later 2026-09-26 scope decision
requires hosted core E2E and visible-window Qt for 1.0 while deferring remote
E2E to post-1.0. The original exception must accompany the 0.23.4 release
decision, not turn
the failed hosted run into a success.

The `0.23.4` citation surfaces were first prepared for 2026-09-24 and
refreshed to the intended 2026-09-25 release date after the local date
changed; if publication slips, rerun the preparation and candidate gates
before tagging. MolSysSuite `policy-v1.4.11` now registers both transition
issues (`uibcdf/molsysmt#237`, `uibcdf/molsysviewer#93`) as `authorized`.
Both candidate callers pin that policy release and synchronize its canonical
guide; the exact central repository checker passes locally for each. The
package metadata and test matrix still target Python 3.14, while the README
badge and its distribution test retain the publicly admitted 3.11–3.13 range.
The badge may add 3.14 only after the coordinated release and independent
channel installations permit central `admitted` status. This branch must not
become the public `main` claim until the exact 20-cell installed-pair gate and
other applicable pre-1.0 release checks pass. npm returned 404 for
`@uibcdf/molsysviewer@0.23.4` when checked on 2026-09-24. No npm package,
Git tag, GitHub Release, or Conda promotion has been created for this
candidate.

The complete local Viewer Python suite passed **2,112 tests with 14 accepted
skips** in 61.43 seconds using 12 workers and explicit source paths for both
candidate repositories plus the released SMonitor `0.16.0` tag. The prior
unisolated run was not used as candidate evidence. MolSysMT's matching local
suite passed 10,225 tests with 11 known skips; its fast release gate passed
13/13. These local results support the source candidate but do not replace
the hosted exact-commit gates or the 20-cell installed-pair rerun. Source-pair
workflow `36061167557` passed Linux and macOS/Python 3.14 but failed Windows
in one release-route test; its other Windows results were 2,100 passed and
23 skipped. Windows resolved the test's `bash -n` invocation to the WSL
launcher, although the promotion script itself runs only on Ubuntu. The test
now asserts that runner identity on every platform, retains its promotion
contract checks on Windows, and checks Bash syntax on POSIX. The matching
MolSysMT test uses the same rule. The failed run cannot be credited as a 3.14
pass; the corrected exact commits need a new hosted Windows run.
The new policy's Ruff 0.16.5 formatting gate exposed three older files in
the Viewer test infrastructure; they were formatted without changing test
behavior. Repository-wide Ruff lint and format checks now pass, and the
focused distribution/release-route modules pass 23/23.
The corrected source-pair run `36062983964` passed Linux, macOS and
Windows/Python 3.14. The first staged noarch `0.23.4` build 0 passed its
recipe test (`36064255601`), the installed-pair run `36065287565` passed
all 20 platform/Python cells, Viewer CI against staged MolSysMT passed all
seven jobs (`36064424260`), and notebooks passed in `36064424563`.
The first MolSysMT full-CI run `36063386092`
exposed its outdated controlled ArgDigest source pin: release 0.12.1 writes
the read-only `hint` property inherited from SMonitor 0.16.0. Published
ArgDigest 0.13.0 fixes this; its exact tag source passed the 27 affected
local MolSysMT contract tests. The complete local Viewer suite passed
2,112 tests with 14 skips, and the matching MolSysMT suite passed 10,225
with 11 skips, using the exact ArgDigest 0.13.0 and SMonitor 0.16.0 sources
and 12 workers. Both components now declare 0.13.0 as the minimum. The
existing build-0 staged files and their passing installed cells remain
technical evidence only; build 1 and the complete exact-pair gates must
replace them before promotion.
Build-1 producers passed in MolSysMT `36102277287` and Viewer
`36102277047`, and the corrected source-pair run `36102309036` passed all
three Python 3.14 platforms. MolSysMT's Rust-wheel run `36102309653` then
found an independent stale sibling-source set in its installed-public-smoke
job. Its PyUnitWizard revision lacks `configure.has_active_policy()`, an API
used at import time by both packages and introduced in PyUnitWizard 0.25.0.
The wheel and Conda minimums are being corrected to 0.25.0 in both projects,
and MolSysMT's smoke will reuse the central controlled-source manifest and
an exact Viewer commit. Build 1 becomes diagnostic only; build 2 and fresh
exact-commit gates are required before promotion.
The subsequent MolSysMT build 3 (`36113593257`) passed all five ABI3
platforms; Viewer build 3 (`36113593292`) passed as noarch. Their exact
installed-pair run `36115388335` passed 20/20, Viewer CI `36115388294`
passed 7/7, notebooks `36115388415` passed, the Python 3.14 source pair
`36113593440` passed all three operating systems, and MolSysMT full CI
`36113593532` and Rust wheels `36113593413` passed. The pre-tag source
review then found `uibcdf/molsysviewer#102`: the committed Viewer runtime
still embedded `0.23.0`, even though Conda and npm rebuild it for `0.23.4`.
The earlier Viewer noarch artifact and pair gates are diagnostic only for
the corrected Viewer source. Regenerate the committed runtime for `0.23.4`,
prove the ordinary Python wheel carries that same version, and rerun the
Viewer producer and exact-pair gates before tagging. MolSysMT's unchanged
build-3 ABI3 artifacts do not need to be rebuilt.
The first Viewer build-4 attempt (`36119181642`) proved the source bundle
check but stopped before packaging: the build environment lacked `wheel` for
the new isolated-wheel preflight. No build-4 Conda file was uploaded; the
environment now declares `wheel` and build 4 can be retried without replacing
an existing staged coordinate.
The pre-final source-pair run `36119181575` passed macOS and Windows/Python
3.14 but failed Ubuntu's browser export comparison: source installation had
no release tag and reported a development version against the committed
`0.23.4` bundle. The manual source-pair workflow now validates that bundle
and locally tags its exact Viewer SHA before installation. This changes the
Viewer candidate SHA again, so all preceding source-pair and Viewer staging
results remain diagnostic until rerun on the new commit.
The corrected Viewer build-4 run `36120275908` did pass the ordinary Python
wheel/runtime check and uploaded its noarch file, but it precedes the
source-pair workflow correction. A new immutable Viewer build number is
required for the final exact candidate; build 4 is diagnostic.

## Separate Python 3.14 staging slice

On 2026-09-24, technical staging-only coordinates were created for the newer
source branches: MolSysMT 0.22.3 ABI3 build 0 on Linux x86-64 (producer run
`35990161344`) and MolSysViewer 0.23.3 noarch build 0 (build and recipe-test
run `35990850975`). An exact Linux/Python 3.14 dry-run resolves both from
`uibcdf/label/staging`. Subsequent exact-pair runs passed Python 3.11–3.14
on Linux x86-64 (`35992241212`), Linux ARM (`35993063086`), Windows
(`35993616429`) and macOS ARM (`35993242687`): 16 installed cells with
explicit environment records. macOS Intel's build (`35992423543`) and
four-cell matrix (`35995465959`) then passed, bringing the exact staging pair
to 20/20 installed cells across five native platforms. Every run retained
four explicit environment records; the MolSysMT validator checked the
staging URL and SHA-256 of both packages. These are five targeted runs, not
a single combined workflow or a public-channel claim. The 3.14 branch
proposal records the source and artifact hashes.
These are not Git tags, public releases, or a decision to ship those version
numbers.

A prior local `devtools/build_against_staging.sh` result remains useful evidence about
the noarch shape and recipe tests, but it is not a substitute for these exact hosted
candidate gates. Neither repository may publish unilaterally merely to turn the other's
CI green.

## Historical validation observed — 2026-08 to 2026-09-19

- Full run on 2026-09-19: **2,067 Python passed, 13 accepted skips, exit 0** in
  63.09 seconds with 12 workers
  (`python -m pytest --receptor=llm -n 12 tests/`). The focused distribution and
  staging-contract slice passes 16 tests; Ruff and the generated devguide indexes pass;
  the Conda recipe renders as one `noarch` build-0 candidate. No artifact was uploaded.
- Previous baseline, 2026-08-15: **1,612 Python passed, 4 skips, exit 0**
  (`python -m pytest --receptor=llm -n 12 tests/`). The `selections.md` failure of
  2026-08-14 is closed: the page called deprecated `add_label()` while the documentation
  harness promotes `DeprecationWarning` to an error, and it now uses the canonical
  annotation manager. The failure was deterministic, not flaky — the warnings-registry
  explanation was tested directly and falsified. The suite ran green three consecutive
  times at 1,611 before the guard below was added.
- Gate 9 was verified by behaviour as well as by count: exercising a broad slice of the
  public surface with `UserWarning` promoted to an error produces no
  `DigestNotDigestedWarning`.
- **No documented example may call a deprecated API** (2026-08-15).
  `test_no_documented_example_calls_a_deprecated_api` reads the deprecations out of the
  package's own warning messages and checks every python block and notebook cell under
  `docs/content` against them, scoped by function — `add_set_alpha_spheres(centers=…)` is
  correct and `add_sphere(centers=…)` is not, so a check on the bare name would flag 59
  correct examples. It found one survivor the running gate could not see:
  `showcase/pharmacophore.ipynb` still called `add_pharmacophore_features()`, now
  `add_interaction_sites()`. Running a page is not what makes its example wrong.
- The Phase 8/9 frontend baseline at that time was **273 JS**, `tsc` clean,
  **30/30 E2E**, `build:runtime` and `test:perf` green. The later 294-JS
  and hosted 34-case core E2E evidence near the top of this checkpoint
  supersedes this as a current release reading.
- Every guard added in this round is mutation-verified; each test says which mutation
  kills it.

## Phase 8 result

The measurement matrix uses 2,882, 26,214, 104,856 and 314,568 atom molecular
supercells, crossed with 1, 10 and 100 structures where feasible. Fixture work
is owned and timed separately as MolSysMT work; no time coordinate is invented.

Main findings:

1. Typed coordinate transport scales well with structure count. At 314,568
   atoms, topology metadata is still 25.3 MiB JSON and Python serialization is
   about 1.63 s. Topology encoding, not `view.molsys`, is the next data-plane
   target.
2. Real Mol*/SwiftShader rendering is the scale ceiling: the 314k x 10 case
   peaks around 5.67 GiB process RSS and first becomes visible in about 31 s.
   Page close removes the scale-proportional renderer process.
3. Slow structure switches are variable first-visit/state-tree work, not a fixed
   1.36 s transport tax. Do not prewarm every structure without an A/B against
   startup and peak memory.
4. Host traffic remains isolated from a 314k popup transfer: 0.0088 ms against
   the fixed 100 ms threshold.
5. Qt assembly still peaks at 2x for representative coordinate-dominated
   payloads. Preallocating `bytearray` does not improve that shape; a future fix
   needs lower-copy delivery.
6. Scene-history snapshots now use compact deterministic JSON bytes and a
   64 MiB combined undo/redo budget. A 100k literal-overlay history dropped from
   about 212 MiB to 52.66 MiB retained RSS. The byte guard is mutation-verified.

## What is next

**Read [`capability_audit.md`](capability_audit.md) before writing any claim about what
MolSysViewer does.** It is generated; regenerate with
`python devtools/capability_audit.py --write`.

**A defect or a proposal is filed under
[`reporting_protocol.md`](reporting_protocol.md)** — front matter, a GitHub issue, and a
`guard` named at close. Adopted 2026-08-14 from MolSysMT; the queue
documents carry it.

Resume toward **1.0** in this order:

**Current session priority (2026-10-07):** the immutable stabilization pair
and its staging/core/provider-source gates are verified in the current handoff above. The
corrected automatic-development hosted follow-up also passes on all three hosts.
Use the fixed Viewer producer `1a4c97a58b68b69f3a836546c9e4ac6187c3efa2` and
MolSysMT producer `46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`; earlier source
handoffs do not replace these artifact identities.

1. Exact canonical-source integration and automatic hosted follow-up 37545069147
   pass. #175 is resolved; native verdicts and Linux notebook/core results are
   preserved. Both fixed packages are now published and independently verified.
2. Both releases are public and source preservation is verified; npm publisher
   #176 is resolved. Viewer build 1 and its public npm/CDN runtime are verified.
   Keep the immutable source/package identities fixed.
3. The sixteen-cell public pair qualification is complete in `37587631519`.
   All actual environment archives and the independent exact-source gate pass;
   preserve this public evidence separately from staging and source results.
4. Done: #114/#140/#151 are resolved and archived with the public package
   evidence, updated Interactions guide and 207 fresh installed checks.
   Preserve earlier experimental/source verdicts and the normative obligation
   to recertify the eventual 1.0 candidate. #142/#144/#145 are also resolved
   with 47 installed workflow/scene checks and the completed user-guide examples.
5. Done: Movie interruption #177 is corrected and qualified on source `7880e2e3`;
   the independent core and three-host Python 3.14 source pair pass. Keep the
   experimental Qt failure separate. #149/#150 are also resolved: the remaining
   applied-recipe alias has installed development-wheel/exact-source evidence;
   the numeric plot contract and #143 multi-card lifecycle are qualified on the
   public pair. #101/#153/#154/#155 are resolved with exact public Windows and
   installed-tool/box evidence; experimental #35 retains its separate scope.
6. Reconcile public documentation and remaining support promises. The five-stage
   human notebook review is complete; retain it. Installed first-contact review
   and final 1.0 candidate qualification remain separate. Standalone is
   experimental; remotes and the Mol* dependency update remain post-1.0.

The older general growth checklist below is a follow-up inventory. It does
not replace this session's ordered priorities.

1. **Widen `EXECUTABLE_PAGES`** in `tests/test_documentation_pages_run.py`. It executes
   three documentation pages today; the rest of the markdown is run by nothing, which is
   how a half-applied rename left a `NameError` in four pages. This is the only remaining
   item that needs neither another machine nor a decision. What the whole tree already has
   is the *static* half — every page parses and none calls a deprecated API — so what
   widening buys is the `NameError` class of defect, which only running finds.

   The current audit lists **three surfaces without a direct browser observation**:
   `save_state`/`load_state`, `save_session`/`load_session`, and units. These are
   persistence/value-policy surfaces; trajectory plot and movie playback now have
   browser evidence. Session remains experimental. See the *Nothing has watched these draw* section of
   [`capability_audit.md`](capability_audit.md), and
   [`archive/evidence_a_stable_capability_has_not_earned.md`](archive/evidence_a_stable_capability_has_not_earned.md)
   (uibcdf/molsysviewer#65), which is the entry that asks for the decision rather than the
   suites.
2. For the later supported standalone-host decision, close Phase 7's two
   observations when the required workstation is available: Qt real-window/GPU
   and ten human live-demo replacements. They are outside the core 1.0 gate.
   Never report existing offscreen/browser evidence as those observations.
3. Complete scientific dogfooding and the remaining human decisions in
   [`what_needs_a_human_2026_08.md`](what_needs_a_human_2026_08.md)
   — three items, all needing a screen or a judgement.
4. Use the published 0.22.4/0.23.4 pair as the dependency-channel baseline;
   do not repeat staging merely to rediscover that it solves. Finish the
   end-user one-line first-contact observation. Evaluate newer aligned
   conda-forge PySide6/Qt through experimental standalone dogfooding
   (`uibcdf/molsysviewer#113`) on its own schedule. For 1.0, repeat the exact
   wheel, Conda, import, resource and public
   installation gates. Use the read-only public-file verifier now shared by
   both promotion workflows (`uibcdf/molsyssuite#48`); never re-upload an
   immutable artifact to change a workflow conclusion.
5. Run `python devtools/release_gate.py` on the new exact 1.0 candidate and
   release 1.0 only when every required gate exits zero. The 0.23.4
   pre-1.0 release carried an explicit, bounded Qt/E2E exception. The strict
   1.0 scope now excludes the experimental standalone host; its E2E scope is
   the core non-remote browser lane. Remote-only E2E remains post-1.0. Before tagging,
   `python devtools/prepare_release.py` sets citation fields; after the
   GitHub Release, verify Zenodo's **public** record rather than treating a
   short ingestion timeout as permanent failure.

Closed in Phase 10 so far: atomic overlay-state file helpers, notebook CI, opt-in hover
telemetry, and public-callable digestion. Hover is runtime/session state rather than scene
state.

*Updated 2026-09-02:* the state helpers were "not a molecular-session bundle" until #38
closed. There is now a second unit rather than a wider first one — `view.save_session()` /
`molsysviewer.load_session()` write a `.msv` carrying the molecular system, while
`save_state` still writes the overlay and the vantage point alone.

### One proposal waiting on a decision, not on work

`what_save_state_promises.md` was the other. Its five decisions were answered on
2026-09-01 and it is now
[`archive/what_save_state_promises.md`](archive/what_save_state_promises.md); the
cheapest and most valuable of them — binding a state document to the structure it was
written from — was answered by re-resolving onto a different structure rather than by
refusing it.

- [`archive/addon_maturity_and_ownership.md`](archive/addon_maturity_and_ownership.md)
  — the maturity vocabulary is defined; each toolkit adopts it by re-declaring
  `meta["status"]`. Until then the README reports what each add-on says today.

## Resume cautions

- Read
  [`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md),
  [`scene_contracts.md`](scene_contracts.md),
  [`data_plane_architecture.md`](data_plane_architecture.md) and
  [`runtime_message_router.md`](runtime_message_router.md) before changing the
  runtime.
- Python remains the authority for reproducible scene state.
- Keep `molsysmt.MolSys` as the scientific authority; optimize wire projections
  instead of introducing a second in-memory truth.
- A sequence of structures need not have time. Missing box and time remain
  missing; never synthesize either for transport convenience.
- Binary buffers are runtime data, never scene history.
- Never validate rendering with `E2E_ALLOW_SKIP=1`.
- If a mutation remains green, first suspect that it hit the wrong layer or a
  stale build artifact.
