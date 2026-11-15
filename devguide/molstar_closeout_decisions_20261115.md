# Mol* qualification: remaining decisions and exact next actions

Current work belongs to #372/#369 and the #315 closure route. The
[three-block receipt](molstar_closeout_three_blocks_20261115.json) records the
observed evidence. This note prepares decisions; it does not grant them or
claim a frozen producer, package, installed pass or publication clearance.

## 1. Complete source receiving

Linux recovery [43692655949](https://github.com/uibcdf/molsysviewer/actions/runs/43692655949)
receives MolSysViewer `21474b8cd4703ee54ed570733e4dbefdeea465ea` with scientific
source `aee7aa65da56e896d1cb2d655bf73736f6453a43` and pandas 3.1.0. It passes
4,752 Python cases and all 25 notebooks, then fails core entry 10 after nine
complete entries. #397 corrects a helper choosing a popup role before actual
bootstrap; its complete affected lifecycle now passes canonically in `903`.
The earlier #395 story correction also passes its complete entry locally.
All 63 core entries remain required in one uninterrupted successful current
run; neither failed prefix nor a local suffix supplies that acceptance.

The corrected full source checkpoint is now
[43698930436](https://github.com/uibcdf/molsysviewer/actions/runs/43698930436),
producer `28147339afe0315c1b252095c1442a1674fc5c9e` with the same scientific
source/pandas and all 63 core entries. It is now terminal failure: 4,760 Python
cases and all 25 notebooks pass, followed by 53 complete core entries. #397's
popup lifecycle passes; entry 54 repeats the independent static bootstrap
timeout tracked under #391. Its new diagnostics observe a controller at
retirement, without captured page/console/network errors. Keep the failed
run and its original verified ZIPs. Do not rerun unchanged inputs blindly.

Real-export control `907` demonstrates that a hidden iframe creates its
controller while the default animation-frame predicate stops polling. The
receiving correction uses timer polling under the same 30-second bound and
adds an actual hidden/revealed molecular export. This does not assign the
original hosted page's visibility; affected and full source gates remain due.

The subsequent complete source checkpoint is now terminal:
[43743095366](https://github.com/uibcdf/molsysviewer/actions/runs/43743095366),
MolSysViewer `f6765f6c680b82f47de0ae94dcd459ac32a79138` with owner-published
MolSysMT `bc5a9297a762d451742734f9e11c7f54c6a832a0`, pandas 3.1.0 and the
>=7.4.0 notebook profile. It selects all three Python 3.14 source hosts, all
63 Linux core entries and 25 notebooks. The first receptor reports three
active jobs; complete exact-head inventories confirm one dispatch. All three
later fail the same stale literal `ipykernel` test expectation, rejecting
the corrected `ipykernel>=7.4.0` recipe. The six original ZIPs match GitHub
hashes. The corrected assertion and four-recipe floor guard pass 549 scoped
checks in `921`; a new exact checkpoint is due. Browser/core entries were not
reached. `source_receiving=true` skips
candidate version/tag assignment; intended 1.0.0 input fields are not artifacts.

After terminal inspection, retain original logs and ZIP/hash/JUnit evidence.
Reconcile #244/#395 against their complete guards and #388/#391 against the
actual diagnostics and remaining causal limits. A successful source gate
does not qualify a different provider or an installed artifact.

## 2. Proposed staging preparation, still subject to its separate approval

The agreed final public pair remains MolSysViewer 1.0.0 / MolSysMT 1.0.0.
The reviewed proposal is **MolSysViewer build 0** and **MolSysMT ABI3 build 1**,
staging only. These are proposed coordinates, not files or reserved names.
The four old MT build-0 files belong to `6dc80725`; preserve them unchanged.
The owner review source `96988b6e` is not yet a frozen MT producer. Current
source receiving uses its later published `bc5a9297` delivery: Git confirms
no package/native/manifest source differences from `96988b6e`. That current
checkpoint requires its corrected successor; earlier `aee7aa65` campaigns do not qualify their 165
changed scientific package files merely through native binary equality.

The existing `prepare_release.py` has prepared and validated a private copy of
five changed metadata/route surfaces for review. Main's citation, release plan,
version metadata and runtime remain unchanged. The date is provisional. This
is a metadata rehearsal, without a Git tag, build, installation or upload.

On approval to resume only staging preparation:

1. Agree the provider's final source and prerequisites with its owner. MT's
   #256 retains the independent BindingMT #73 omitted-version native-write
   and whole-file migration controls, ordinary and pm/fs. Do not perform or
   waive another component's scientific acceptance from this session.
2. Prepare the reviewed citation/route metadata and versioned runtime from a
   clean independent candidate, using the supported build command and wheel
   validator. Select a final immutable producer/ref after that review. Keep
   shared editable environments and all public refs unchanged.
3. Receive the exact final source and required wheel/runtime/dependency gates.
   MT retains ownership of its recipe/build change and producer. Deliver any
   proposed MT patch as a PR; never push or merge its main here.
4. Build only new staging coordinates; independently receive every original
   file, source mapping, build, channel and SHA-256 before installation tests.
5. Agree one installed 16-cell dispatch (four platforms, Python 3.11–3.14),
   then independently inspect all required steps, original environment ZIPs,
   public/staging URL origins, versions/builds and digests. Source overlays
   cannot supply this result. Perform the separately required minimum/newer
   consumer qualification for #524.

The original public MolSysViewer 0.24.0 build 1 does not declare `closed`;
that minimum-host gap is confirmed against the original archive and registry.
Its first source implementation is `60659082`. The first compatible new
published floor is still pending an actual delivery and installed check.
Conversely, original MolSysMT 0.23.0 already exposes the consumed native
ChemicalStates/get_bonds boundary. Do not raise its minimum just because a
public namespace was introduced later. The artifact inspection qualifies
neither complete runtime compatibility nor all optional capabilities.

The packages have a two-way runtime dependency. If MT's first compatible
published host floor becomes 1.0.0, recheck the eventual public promotion order
against both actual manifest floors. Do not reuse the old MT-first sequence
without checking whether the first promoted package has a public solver
closure. Joint staging can receive both files; that does not make a temporarily
missing public counterpart installable. Agree the coordinated availability
and verification sequence before the separate public authorization.

Staging approval would leave **public tags, GitHub Releases, npm/CDN,
main-label promotions and both public 1.0 publications paused**. Source-only
CI authorization has not already lifted the staging construction pause.

## 3. Historical startup uncertainty and actual-host acceptance

The [#384 audit](pending_bugs/initial_jupyter_canvas_timeout_audit.md) separates
MolSysMT #615's missing original pre-deadline trace from a fixture exception
and the independently proven/fixed #392 source-reply lock defect. The original
timeout cannot be assigned to either from the preserved evidence. Current
normal/contended startup passes are useful controls, not a historical cause.

The maintainer's [decision recorded by MolSysMT](https://github.com/uibcdf/molsysmt/blob/c80e7380a/devguide/pending_bugs/intermittent_jupyter_initial_canvas_timeout.md#maintainer-decision-continue-the-investigation--2026-11-15)
keeps #615 open and requires further investigation; the proposed historical
disposition is not accepted or awaiting approval. #384 leads the causal work.
Keep #392's causal regression and the strengthened #754/#762 observations;
do not raise the 30-second canvas deadline, retry blindly or describe the old
failure as fixed. The next control distinguishes initial execute admission
from molecular preparation, bootstrap and drawing. Candidate receiving still
requires a real eligible draw after scene registration within the same bound.

That discriminating work now demonstrates the old-kernel mechanism in the
kernel-only `919` and actual TcTIM/Jupyter `923` controls. The correlated
execute is admitted after 30.52 seconds with 7.3.0, but after 1.6 ms with
7.4.0; the latter renders all 3,983 atoms on a new draw in 6.55 seconds.
Preserve `923`'s combined exit 1 from its post-retirement marker assertion;
`924` verifies the actual pre-deadline/late-entry timing offline, without a
rerun. This is controlled scheduling, not a spontaneous recurrence or proof
of the original history. Review the [causal evidence](pending_bugs/initial_jupyter_canvas_timeout_audit.md#actual-jupytertctim-overlap--2026-11-15)
with MolSysMT; #615 stays open and no historical waiver is pending.

Actual Jupyter and native Wayland/Qt/NVIDIA source receiving retain exact
input identities. Recheck changed boundaries: the current runtime changes
Movie's editor since the preceding Qt receipt. Automated capture is distinct
from human inspection. Qt remains experimental; v6 remains post-1.0.

Current native Qt receiving `888` passes. The additional actual-Jupyter Movie
guard `889` finds a pending seek after its first two phases, tracked separately
in [#396](pending_bugs/jupyter_movie_seek_pending.md). This must be investigated
and received before claiming current actual-host Movie acceptance. It does not
explain the older first-canvas #615 observation or invalidate the narrower Qt
result. A source core pass alone would not close this live-kernel boundary.

The current investigation now reproduces the comm/execute stall independently
on ipykernel 7.3.0. The original 7.4.0 provider, incorporating upstream #1529,
passes 30 native comm cycles and the maintained complete Movie guard in `916`,
including ten same-kernel Python-edit/seek cycles. The component notebook
recipes require `ipykernel>=7.4.0`. The unchanged shared legacy prefix remains
on 7.3.0; [MolSysSuite #200](https://github.com/uibcdf/molsyssuite/issues/200)
owns its controlled migration. This is a received source-host solution, not
an installed-candidate gate or a cause assigned to the older #615 observation.

Prepare the postponed human round against the received artifact, rather than
an unrelated development overlay. It should cover the already agreed molecular
edit review/cancellation/application and independent new-view result; primary,
canvas-popup and detached-Studio ownership; and the actual Movie preview,
session recovery and exported appearance. Use the owning prepared scenarios
and retain scientific parameters and source data. A short checklist must not
silently replace E4's accepted workflow. Resume when the maintainer chooses,
or record an explicitly accepted scoped disposition. Neither automatic tests
nor continuous-development authorization count as that human observation.

## Closure

Only completed source, installed, compatibility and applicable host/human exits
close #372, followed by reconciliation of #369. The 39/46 source-delivered
and 1/46 final-acceptance counters do not move because a preparation document,
single guard or prefix passes. Public publication retains its later decision.
