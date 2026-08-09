# Opt-in hover telemetry

**Status:** implemented on 2026-08-09. The selected policy is explicit
`telemetry_disabled` state, default-off transport, and automatic activation
while at least one Python callback is registered.

**Origin:** the scalability note in
[`../interaction_targets_and_selection.md`](../interaction_targets_and_selection.md)
§`hover_target`. Promoted to its own proposal on 2026-07-31 because the July
transport round attacked the same problem from a different angle and only solved
half of it — which is exactly the kind of partial fix that gets mistaken for a
closed one.

## The problem

Every debounced hover is forwarded to the kernel. The frontend debounce is
60 ms, so continuous hovering is ~16 messages per second crossing the Comm
channel. On a remote or high-latency deployment (cloud JupyterHub) that competes
with everything else the kernel is doing, and most sessions never read hover
from Python at all — they use it for frontend tooltips.

## What already landed, and why it is not enough

Mol\* re-emits hover on every resolved pick, storing `prevLoci` but never using
it to suppress. A mouse **resting** on one atom therefore produced ~30 identical
messages per second. `registerInteractionObservers`
(`js/src/managers/viewer-controller.ts`) now deduplicates the Python-bound
projection by comparing the serialized payload; local UI still sees every tick.

That fixes the resting mouse completely and the **moving** mouse not at all:
while the pointer travels across the structure every tick is a genuinely
different payload, so nothing is suppressed and the original ~16/s remains.
Deduplication and opt-in are complementary; opt-in is the one that addresses the
case the note was written about.

## The proposal

Forward hover to the kernel only when someone is actually listening:

- a Python callback is registered (`view.on_hover(cb)`), or
- telemetry is explicitly enabled (`view.hover_telemetry_enabled = True`).

The frontend is told which state it is in, so the suppression happens **before**
the message is sent, not after it arrives.

## Decision

`view.hover_target` became a public query object *after* the original note was
written, and it is populated **from** the forwarded events. Gating forwarding on
`on_hover(cb)` alone would leave `view.hover_target.info()` silently empty for
anyone who queries it without registering a callback.

That trades a performance problem for a correctness one, and it is precisely the
failure `scene_contracts.md` Contract S7 forbids: an empty target that *looks*
like "nothing under the cursor" is indistinguishable from the truth, and the user
has no way to tell. **A plausible wrong answer is worse than a loud one.**

The decision is: **`view.hover_target` reports the transport state honestly
when telemetry is off.**

- an explicit "telemetry disabled" state that `info()` reports honestly — the
  query still answers, and it answers about itself;
- or `hover_target` counts as a listener, so merely touching it turns telemetry
  on for the rest of the session (discoverable, but surprising);
- or telemetry defaults on and the flag is opt-*out* (no correctness risk, no
  default gain).

The first option was selected. `info()` reports `kind="telemetry_disabled"`
while off and `kind="telemetry_waiting"` after activation but before the first
sample. `is_empty()` raises in both states because neither means that the cursor
is over empty canvas. Merely reading `hover_target` never changes runtime
behavior.

The frontend gate covers canvas and hierarchy-panel hover sources before the
widget seam. Disabling cancels a pending debounce, and Python rejects any late
hover event already in flight. Registering the first `on_hover` callback enables
the channel; removing the last disables it unless the explicit flag remains
true. This is runtime/session state and is reprojected to canvas endpoints, but
is deliberately absent from scene-state serialization.

## Acceptance

- With no callback and telemetry off, hovering sends **zero** hover messages to
  the kernel, verified by counting messages at the seam, not by timing.
- `view.hover_target.info()` never reports "nothing hovered" when the truth is
  "not being told" — mutation-verified by disabling telemetry and asserting the
  reported state changes shape.
- Registering `on_hover` mid-session starts forwarding without a reload.
- The existing deduplication stays: it is what keeps a resting mouse quiet once
  telemetry *is* on.

Five guards were mutation-verified: removing the frontend gate, the Python
late-event guard, the explicit disabled state, callback-driven activation, or
strict boolean validation made its focused test fail. The live AnyWidget seam
also observed zero hover envelopes before enablement and exactly one after it in
real Chromium.
