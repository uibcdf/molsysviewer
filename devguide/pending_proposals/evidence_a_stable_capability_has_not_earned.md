---
summary: Four capabilities declare an evidence level nothing has observed, and the release gate cannot tell.
issue: uibcdf/molsysviewer#65
status: open
opened: 2026-09-01
closed:
verification: measured
area: [tests, process]
guard:
normative:
blocked_by: []
supersedes: []
---

# A `stable` capability that nothing has watched

**Reported:** 2026-09-01, while triaging what remains before 1.0. The four rows were
already named in [`capability_audit.md`](../capability_audit.md); what was missing was an
entry that could be assigned, and the observation that the gate cannot see them.

**Status:** open. Nothing is broken. The claim is what is unearned.

## What

Four capabilities carry no browser observation. Measured against the 30 E2E suites in
`molsysviewer/js/tests/e2e/`:

```bash
$ cd molsysviewer/js/tests/e2e
$ for k in trajectory_plot movie save_state export_state; do
    printf "%-16s %s suites\n" "$k" "$(grep -rl "$k" *.e2e.ts | wc -l)"; done
trajectory_plot  0 suites
movie            0 suites
save_state       0 suites
export_state     0 suites
```

Two of the four — `save_state`/`load_state` and units — are declared **`stable`**, which
`capability_audit.md` defines as *"the public surface is documented, digested and covered
by tests, and changing it is a deliberate act"*.

The audit already states the position honestly: the two `stable` rows are defensible
*because neither draws anything*, "but it is the kind of claim that should be made on
purpose rather than inherited". **Nothing has made it on purpose.** That is this entry.

## How

Four rows, four different decisions. Treating them as one backlog of E2E suites is the
mistake to avoid: two of them should never get a suite.

| Capability | Status | Draws | What it needs |
|---|---|---|---|
| Trajectory plot | `experimental` | yes | An E2E. The runtime already accepts `set_trajectory_plot`. |
| Movie | `experimental` | yes | An E2E for playback: `play_movie` / `stop_movie` exist. **Export stays out** — it depends on an external encoder and `capability_audit.md` already records that it is not exercised in CI. |
| `save_state` / `load_state` | **`stable`** | no | Nothing to observe. Record why, and that the label is chosen. |
| Units | **`stable`** | no | Same. |

The two that draw are bounded work against a harness that already exists. The two that do
not draw need a sentence each, in a place a reader will meet — not in this document.

### The half that outlives the four rows

`devtools/release_gate.py` runs eleven checks: the Python suite, the generated indexes,
citation metadata, version coherence, `tsc`, the JS suite, the runtime build, the
performance gates, every E2E suite, the Qt render observation and the conda artefacts.

**None of them asks whether a capability declared `stable` carries the evidence it
claims.** The audit derives four of its five evidence labels from the repository, so the
data is already there; nothing consumes it as a gate. So the next capability can be born
`stable` with no observation and reach a release the same way these did — inherited
rather than chosen.

## Why

For a viewer, what it draws is the product. `capability_audit.md` calls this "the sharpest
gap there is" and gives it a section of its own rather than a column, precisely because a
count would hide it.

The cost of leaving it is not a defect today. It is that 1.0 converts an inherited claim
into a published one: `stable` is the level at which the audit says *"someone else could
depend on it and find out from us before it changed"*. Two capabilities carry that
sentence without anyone having watched them.

## What is measured and what is assumed

**Measured** — the suite counts above, on 2026-09-01, against 30 E2E suites; the eleven
checks of `release_gate.py` from `--list`; the four rows and their labels from the
generated `capability_audit.md`.

**Assumed** — that an E2E for the trajectory plot and one for movie playback are ordinary
work against the existing harness. Both ops exist on the wire and the harness drives real
Mol\*, but neither has been attempted, so the estimate is an estimate.

**Not established** — whether either capability is actually broken. Nothing here reports a
defect; the four rows may all work perfectly. That is the point: nobody can say.

## What was refuted

**"Write four E2E suites."** Two of the four draw nothing. A suite that opens a browser to
observe `save_state` would assert on a JSON document the Python suite already round-trips,
and its existence would suggest the label had been earned by observation when it was
earned by argument.

**"Promote the two `stable` rows to `browser-observed` once the suites exist."** They will
never be `browser-observed`, because they never draw. The labels are documented as
independent, not as a ladder — a capability may be benchmarked and never observed. The
correction is to state which labels each row can earn at all.

**"Make it a column in the audit."** It was a column and became a section, deliberately:
a count cannot distinguish "not observed" from "not observable".

## Scope and exclusions

**In scope:** the four rows, and a gate that fails when a `stable` capability declares
evidence it does not carry.

**Out of scope:** movie *export* in CI, which needs an external encoder; the Qt render
observation, which is Phase 7's and needs a screen; widening the evidence labels beyond
the capability audit, which is [`evidence_labels_beyond_the_capability_audit.md`](evidence_labels_beyond_the_capability_audit.md)
and must not be merged into this.

**Deliberately not proposed:** raising or lowering any capability's `status`. Whether
`save_state` deserves `stable` is a judgement for whoever answers
[`what_save_state_promises.md`](what_save_state_promises.md); this entry only asks that
the answer be written down.

## Acceptance criteria

1. Trajectory plot and movie playback each have an E2E that drives real Mol\* and asserts
   what appeared, not the message that was sent.
2. `save_state`/`load_state` and units each state, where a reader meets the claim, which
   evidence labels they can earn and which they never will.
3. `release_gate.py` fails when a capability declares `stable` without the evidence its
   own audit derives for it. This is the `guard`, and it is what makes the other three
   more than a one-off tidy-up.
4. The guard is mutation-verified: declare a capability `stable` with no evidence and the
   gate goes red.

## Dependencies and risks

No `blocked_by`. The risk is scope: this entry is about evidence, and it sits next to a
question about what `save_state` promises. Answering that question may change a row's
`status`; it does not change what this asks for.

## Provenance

Measured 2026-09-01 on the shared MolSysSuite development host, Linux, Python 3.13.14,
MolSysViewer at `d082b245`-era `main` (`0.20.1+66`), 30 E2E suites present.
