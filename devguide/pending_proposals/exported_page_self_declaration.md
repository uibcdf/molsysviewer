# An exported page should declare what it is and what it can do

**Status:** **Part A done 2026-08-05, Part B's seam done 2026-08-06.** Part B's
trigger had already arrived and nobody had noticed — see below. Both were deferred because they guard failures that were not
active yet, and the conditions that end each deferral are recorded below; Part
A's arrived when MolSysMT began publishing from this mechanism, and it was
implemented the same day.

**Origin:** deferred from
[`embedding_views_in_external_documentation.md`](../archive/embedding_views_in_external_documentation.md)
on 2026-08-03 — its execution step 2, plus a second item raised in the same
conversation. They are filed together because they are one idea seen from two
sides: **the exported page tells the reader the truth about itself.** One about
the runtime it is running, one about the actions it can complete.

---

## Part A — Scene and runtime may drift, and nothing notices

An export that shares a runtime addresses it. Every export re-places that asset,
overwriting it when the installed version differs, so the asset always matches
whoever exported **last**. (A self-contained export carries its runtime and
cannot drift; since 2026-08-04 that is the whole of the difference between the
two shapes, which narrows this to shared sites but does not remove it.)

That is correct for the view being exported and silently wrong for the others.
Regenerate one view of a documentation site after upgrading MolSysViewer and the
remaining, untouched pages now point at a runtime newer than the scenes they
carry. Nothing compares them.

This is not the old CDN defect returning. There the URL was dead and the page
said so. Here the runtime loads perfectly and renders a scene it may interpret
differently — the failure is quieter, and quieter is worse.

**Proposal.** The exported HTML declares the version that produced its scene.
The runtime compares it with its own on boot and reports a mismatch through the
channel it already uses for a failed load — `console.error` plus a visible line
in the mount element — rather than rendering something plausible.

**Why deferring was safe until 2026-08-05.** Nobody had a multi-view site on this
mechanism: our own views were regenerated in one pass, and MolSysMT had not
adopted it.

**It is not safe now.** MolSysMT has adopted the mechanism and publishes from it,
and the moment they regenerate *one* view after upgrading MolSysViewer — which is
exactly how a documentation site evolves, one figure at a time — their untouched
pages carry scenes older than the runtime placed beside them, with nothing
comparing the two. This is the condition this paragraph was written to detect.
Their site is also where the failure would be quietest: the runtime loads, the
molecule appears, and only the interpretation may have moved.

**Done 2026-08-05.** The exported page declares `scene_version` in its UI block,
and the runtime — which until now knew no version at all, so the build injects one
from `_version.py` — compares them on boot. On a mismatch it writes to the console
and appends a visible line naming both versions, then renders anyway: refusing to
draw would punish the many pages that are a patch apart for the sake of the few
that are not, and the scene is usually fine. What is not fine is not being told.

Compared on the release, not the exact build. A development install rebuilds its
runtime constantly against an unchanged `X.Y.Z`, and warning on that would teach
everyone to ignore the warning that matters.

**Acceptance, met.** `tests/test_exported_page_opens_from_disk.py` pairs a scene
marked `0.19.0` with the current runtime in a real browser and the page reports
it; a matching pair stays quiet. Mutation applied: with the comparison removed
both tests go red, and green again when restored.

**Note for the `cdn` path.** It cannot produce this mismatch: the URL is pinned
to the exact version that exported the page, so scene and runtime agree by
construction. This guard exists for a shared local runtime, which is the one that
gets replaced underneath pages nobody touched.

## Part B — The page offers controls it cannot honour

`bootDocsView` builds the controller with an empty notify callback
(`index.ts`: `MolSysViewerController.create(target, () => {}, ...)`). That
callback is the channel to Python. In an exported page there is no authority, so
everything that would reach Python reaches nothing, without a diagnostic.

**Measured, and better than feared.** A default export carries
`panel_mode_style` absent or `"drawer"`, and `viewer-controller.ts` only builds
the `FloatingPanelShell` for `floating`, `floating-unified`, `integrated`,
`ambient` or `split`. So today an exported page shows Reset, Fullscreen, Spin,
Swing, Help, popout and the trajectory bar — and **all of those work**, client
side. The popout genuinely works: it loads the same runtime by URL and syncs
peer to peer over `postMessage`, with no Python involved.

**The honesty is accidental.** Three things end it, none hypothetical:

1. An author exporting from a view configured with `panel_mode_style="integrated"`
   (or floating, ambient, split) **does** get the Studio shell in the static
   page, and most of its panels need authority.
2. The Canvas UX direction moves toward `integrated` as the default, which turns
   that from the exotic case into the normal one.
3. In `cinema` mode the page tells the reader *"Press N/W for panels, H for
   help"* — advice that may lead nowhere on a page with no kernel.

So the current good behaviour rests on the default of one field, and the roadmap
removes it.

**Proposal.** An exported page surfaces only what it can complete, decided
deliberately rather than by a default. The classification does not need
inventing: `runtime_actions.json` already lists every browser→Python action, and
that list *is* the set that needs an authority. Whatever cannot be classified
cleanly should report instead of staying silent.

**Important nuance.** "Panels do not work without Python" would be wrong. Hiding
a region already present in the scene is local and works; naming a new selection
needs authority. The manifest distinguishes them, and the fix must too — hiding
a working control is its own kind of dishonesty.

**Why deferring was safe when this was written.** The default export exposed
nothing dead, because `panel_mode_style` defaulted to `drawer`.

**It stopped being safe, and the file did not notice.** The condition written
here was "the moment `panel_mode_style` defaults to `integrated`". Measured
2026-08-06: a plain `MolSysView()` reports `panel_mode_style="integrated"` — the
trait declares `"drawer"` and construction overrides it — so **every export
already builds the Studio**. Its DOM carries "Studio" twenty times. Meanwhile
`bootDocsView` still created the controller with `() => {}`, so all 127
`ctx.onAction` call sites across ten panels emitted into nothing.

**Done: the seam.** The reporter passed to `MolSysViewerController.create`
consults the manifest and, for a command that needs an authority, shows a notice
naming the action, saying there is no Python behind the page, and pointing at a
notebook, the desktop application and
[uibcdf.org/molsysviewer](https://www.uibcdf.org/molsysviewer). One funnel, so
nothing can go silent again.

The distinction that made it honest is new manifest data, `frontend_authoritative`:
a measurement, a section drag and an active-selection pick are performed by the
browser and merely reported to Python, so they **work** in an export and warning
about them would tell the reader they cannot do what they have just done.
`needsRunningSession` is unit-tested over all six cases and mutation-verified.

**Still open: the polish.** Controls whose action is knowable at construction —
representation, delete region, apply query — should be disabled with their reason
rather than inviting a click that reports. The seam makes that an improvement
rather than a rescue. And what the panels *display* stays untouched: that
information is correct and hiding it would be the other kind of lie.

## Not in scope

- A reduced "docs runtime" build. Measured from the bundle source map: molstar
  is **76.7%** of it and our own sources **20.8%**, so a docs-only entry point
  could shave a fraction of a fifth and would not change the order of magnitude.
  If the exported page should carry less, the argument is honesty, not size.
