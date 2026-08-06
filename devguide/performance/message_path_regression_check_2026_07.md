# Message-path regression check after the runtime envelope — July 2026

## Why this exists

`engineering_rules.md` §6 requires `npm run test:perf` whenever a change touches
the message path, and the harnesses exist because of a real defect:
`handleMessage` once carried a **~3-second-per-message** toll that polluted every
"is it fast enough" judgement in the project.

The R1/R2/D3/D4 round touched the message path about as hard as it can be
touched: every outbound message now goes through `wrap_outbound`, every inbound
one through `WidgetRuntimeRouter`, the popup channel validates action against
direction, and hover projections are deduplicated. That is exactly the shape of
change the harnesses guard against, and it was **not** measured when the work
landed — the omission was caught by re-reading the rules, not by any check.

## Command

```bash
cd molsysviewer/js && npm run test:perf
```

## Measurements (2026-07-31, linux)

`message-toll.perf.ts`, 95,000 atoms:

| Quantity | Value |
| --- | --- |
| Load | 3404.9 ms |
| **Unknown-message toll** | **0.3 ms** |
| Hide | 0.2 ms |
| Group nodes | 9,500 |

`dynamic-region-frame.perf.ts`, 1000 frames / 1000 messages:

| Quantity | Value | Budget |
| --- | --- | --- |
| Per-frame evaluation | 0.0008 ms | 16 ms frame, 25 ms cap |

## Reading

The envelope did **not** reintroduce the toll. The per-message cost is 0.3 ms,
four orders of magnitude below the defect the harness was written to catch, and
per-frame dynamic-region evaluation is effectively free against its budget.

This is the expected result rather than a lucky one: enveloping adds a dict
wrap, a counter increment and a membership test per message, and
`_MESSAGE_SEQUENCE` was deliberately an `itertools.count` instead of `uuid4`
(measured 12× cheaper) for this reason. But "expected" is not "observed", and
the rule asks for observed.

## The transferable lesson

The harness caught nothing here, and that is not an argument for skipping it.
Its value is that a *future* regression in the message path now has a tripwire
whose baseline was taken **after** the envelope, not before it: without this run
the next measurement would have had no honest point of comparison, since the
last one predates the whole protocol.

Re-run it when touching the message path, region ownership masks, or per-atom
colour.

---

## Re-measured 2026-08-06, after the render-path round

`engineering_rules.md` §6 asks for this after message-path work, and four
changes had landed since the July baseline without it: camera authority
(Contract S9), in-place representation update, add-before-remove succession
(Contract S10), and the hierarchy relay.

Same machine, same command, same 95,000 atoms:

| Quantity | 2026-07-31 | 2026-08-06 |
| --- | --- | --- |
| Load | 3404.9 ms | 3388.5 ms |
| **Unknown-message toll** | **0.3 ms** | **0.3 ms** |
| Hide | 0.2 ms | 0.3 ms |
| Group nodes | 9,500 | 9,500 |
| Per-frame dynamic-region evaluation | 0.0008 ms | 0.0007 ms |

Nothing moved. Load is 0.5 % faster, which is noise at one sample, and the two
sub-millisecond figures are at the harness's resolution — a 0.1 ms difference on
`hide` is one tick, not a trend.

The result was not obvious in advance: add-before-remove succession means a
representation change now builds the new one *before* dropping the old, so the
question was whether the extra transient object showed up in the message path.
It does not, because the succession happens inside the state handler and never
crosses the seam as extra messages.
