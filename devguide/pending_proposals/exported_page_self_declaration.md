# An exported page should declare what it is and what it can do

**Status:** open, deliberately deferred. Neither half blocks the work that
unblocks MolSysMT, and both guard failures that are not active today. They stop
being safe to defer for reasons recorded below.

**Origin:** deferred from
[`embedding_views_in_external_documentation.md`](embedding_views_in_external_documentation.md)
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

**Why deferring is safe today.** Nobody has a multi-view site on this mechanism
yet: our own views are about to be regenerated in one pass, and MolSysMT has not
adopted it. The first site that regenerates a *subset* is when this starts to
bite.

**Acceptance when it is done.** Pair a scene with a deliberately mismatched
runtime and the page reports it. Mutation: remove the comparison and that test
must go red.

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

**Why deferring is safe today.** The default export exposes nothing dead.

**Why it stops being safe.** The moment `panel_mode_style` defaults to
`integrated`, or the moment anyone exports from a view that sets it. Whoever
changes that default should read this file first; today it is a cheap guard,
after the change it is a rescue.

## Not in scope

- A reduced "docs runtime" build. Measured from the bundle source map: molstar
  is **76.7%** of it and our own sources **20.8%**, so a docs-only entry point
  could shave a fraction of a fifth and would not change the order of magnitude.
  If the exported page should carry less, the argument is honesty, not size.
