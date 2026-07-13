# Engineering rules

`development_mantra.md` says what MolSysViewer *is*. This page says how we are allowed to build it.

These rules are not style preferences. Each one is here because breaking it produced a real defect
that shipped, and in most cases shipped **green** — with a passing test that proved nothing. They
were forged during the 15-phase scene rework (2026-07-10 → 2026-07-11) and were the standing rules
of every one of its phases; they are kept here now that the plan that carried them is gone.

---

## 1. The layering rule: API first

A capability is a **public Python method** before it is a `core.py` handler, and a handler before
it is a GUI control. In that order, no exceptions.

**The GUI never reaches past the public API.** No open-coded loop in TypeScript doing by hand what
a public Python method already does. If the frontend needs a capability that Python does not
expose, the fix is to expose it in Python — not to reimplement it in TS.

*Why:* the System subpanel's colour-scheme dropdown called Mol\* directly for months. The result
was a molecular colour theme that was not in the API, not serialised, not undoable, and silently
destroyed by any per-atom colouring. It took a whole phase to unwind. See
`scene_contracts.md` §0.4.

## 2. Contracts are normative

`scene_contracts.md` governs representation states, colour ownership, ordering and serialisation.
Code that contradicts it is a bug. Changing the behaviour it describes means **editing that file in
the same commit** and declaring the change in its §Migration table.

**Breaking changes are declared, never softened.** No shims, no deprecation periods. MolSysViewer
has no external users; a shim buys nothing and hides the break.

## 3. Never hand-edit generated artefacts

`molsysviewer/viewer.js` (and its `.map`) are **generated**. Edit the TypeScript under
`molsysviewer/js/src/` and run `npm run build:runtime`. See `js_runtime_build_and_version_sync.md`.

**Rebuild as the last step, after the last TS edit.** A `viewer.js` that is out of sync with its
own source is invisible to the test suites — the unit tests import from `src/` — but it is exactly
what the real Jupyter widget executes. This has shipped at least once: a delivery whose `viewer.js`
was ~10 KB behind its own source, with every test green.

---

## 4. Tests

### A test whose name claims an outcome must assert that outcome

`test_region_reset_representation_restores_base_visual_state` passed for months while asserting
only the emitted message dict. The visual outcome its name promised was never checked — and was
in fact wrong.

Claims about what is *rendered* are asserted against the simulated Mol\* plugin
(`js/tests/unit/state-handler.test.ts`) or against the real one
(`js/tests/e2e/scene-contracts.e2e.ts`, which reads `transform.params.type` off the actual cells).
**Never assert only the message dict.** A test that reads back the message it just sent proves the
message was sent.

### Never `as any` + `?.()` on internal APIs in tests

```ts
await (controller as any).someInternal?.();   // ← forbidden
```

If the method is renamed or removed, `?.()` makes the call a silent no-op and the test stays green
while testing nothing. This exact combination produced a green e2e that exercised none of the code
it claimed to cover.

### Watch for the silent skip

An e2e that "skips" when the browser will not launch, or when WebGL is unavailable, reports success
while looking at nothing. If a test exists to confirm something **on screen**, it must **fail** when
it cannot see the screen, not pass. `scene-contracts.e2e.ts` asserts WebGL2 is present for exactly
this reason.

Related trap: the group-panel chrome only becomes visible **after a system is loaded**. An e2e that
forgets `load_molsys_payload` waits on an invisible element, times out, and — depending on how it
is written — can look like a skip rather than a failure.

### Integration seams

A new field crossing Python → panel must survive **every** field-by-field mapping on the way. There
have been two such seams (`state-handlers.setRegionSummaries` and the map in `viewer-controller`
that feeds the panel), and a field was dropped at *both* on the same day. A unit test that calls
`panel.setRegions(...)` directly bypasses them and will not catch it. **Drive the seam, not the
destination.**

---

## 5. The audit method: mutation

This is the single practice that caught every real defect of the scene rework.

> **Revert the mechanism. Its test must go red.**

If a test survives the deletion of the thing it names, it is decoration. Apply it to your own work
before handing it off, and apply it to work you are reviewing before approving it.

What it caught, when nothing else did:

- a `frame_dependent` filter whose test still passed with the filter removed, so a topological
  region would have silently re-evaluated on every frame;
- a sticky-flag fix whose test asserted the flag turned *on* but never that it *cleared*;
- `contains` / `is_composed_of` shipping as permanently empty dicts, because a bare `except`
  swallowed the exception and the test asserted only `isinstance(…, dict)` — which `{}` satisfies;
- a canvas-wide colour wipe that could not be undone.

### When to mutate: **mutate what *prevents*, not what *produces***

Mutating everything is expensive and it generates noise. The rule that keeps the value and drops
most of the cost:

| the mechanism | mutate it? | why |
|---|---|---|
| **a guard** — an `if`, a filter, a check that *prevents* a bad outcome | **yes, always** | It is **invisible when it works.** Delete it and nothing looks wrong: the feature still works, the suite stays green. A guard wired to no test is indistinguishable from a guard that does not exist — and the only way to tell them apart is to remove it and look. |
| **a feature** — code that *produces* a good outcome | no | If it breaks, it shows. Its ordinary tests already cover it. |

**Why this matters more than it sounds:** a broken guard fails **silently**, months later, far from
the change that broke it. And a guard is exactly what a future refactor deletes, because a lone `if`
with no test attached looks redundant.

This is why Contract T (identity) demanded it end to end: **the whole contract is a guard.** Keying
by `(domain, tag)` adds no capability — it only *prevents* aliasing. Rip it out and everything keeps
"working". The panel phases, which are mostly visible behaviour, need far less of this.

**Evidence (2026-07-12, Phase 0 commit 2):** three mechanisms mutated. Two were confirmations. The
third — the only actual *guard*, the `kind` filter in the history rewriter — was **wired to no test
at all**: with it removed, renaming the shape `site1` corrupted the annotation `site1`'s
`layer_tag`, silently poisoning the replay, the HTML export and the popup, **and all 17 tests stayed
green**. The test that claimed to cover it asserted the record's `tag` while the corruption happened
in `options["layer_tag"]` — a different channel.

Three corollaries:

- **Verify documentation against the code, not against the plan.** Executing each claim a doc page
  made is what exposed a real Contract A defect: the docs were right and the *code* was wrong.
- **Never `git checkout <file>` to undo a mutation.** It reverts to HEAD and destroys uncommitted
  work. Copy the file aside first (`cp file /tmp/backup`) and restore from the copy.
- **Mutating the frontend: rebuild the *harness*, not the runtime.** The e2e suites load
  `tests/e2e/harness.bundle.js` (`npm run build:harness`), **not** `molsysviewer/viewer.js`. Mutate
  `js/src/`, run only `build:runtime`, and the mutation never reaches the browser — you will conclude
  a sound e2e is hollow. This nearly produced a false accusation during the Phase 0 audit.

---

## 6. Green means all of it

Before a change is done, all of these pass, and you have **observed** them pass — reporting a suite
you did not run is worse than not running it:

```bash
pytest                     # Python suite
npm run test:js            # JS unit tests
npx tsc --noEmit           # the baseline is ZERO errors. A new error is yours.
npm run build:runtime      # regenerate viewer.js (last, after the final TS edit)
```

And, when the change touches rendering, interaction or the scene contracts:

```bash
npm run test:e2e:all       # 14 suites against real Mol* (PW_CHROMIUM_BIN=/usr/bin/google-chrome)
npm run test:perf          # the message-toll and dynamic-region-frame harnesses
```

## Performance

`js/tests/perf/` holds the harnesses, and they exist because of a real defect: `handleMessage`
carried a **~3-second-per-message** toll that polluted every "is it fast enough" judgement in the
project. It is fixed; `message-toll.perf.ts` is what stops it coming back.

`dynamic-region-frame.perf.ts` guards the per-frame budget for dynamic regions (Contract R): the
frame budget is 16 ms, and per-frame evaluation is capped at 25 ms
(`viewer/core.py:_dynamic_region_evaluation_budget_ms`) before the viewer warns, reports through
SMonitor, and freezes the region to `static` rather than dropping frames.

Run `npm run test:perf` when you touch the message path, region ownership masks, or per-atom
colour.
