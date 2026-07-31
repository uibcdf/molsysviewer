# Build the JSON payload only when it is actually needed

**Status:** open, pre-1.0 candidate. Found 2026-07-31 while measuring startup.

## The question that surfaced it

*"I thought we were no longer going to use ViewerJSON, since MolSys is enough."*

Half right, and the half that is wrong is costing a second per load.

**MolSys is enough — that half is settled.** `loaders/array_native_molsys.py`
does not contain the string `ViewerJSON` at all. D1 serializes the topology once
and the structural arrays directly from `molsysmt.MolSys`, which is exactly the
point of the data plane.

**But ViewerJSON was never removed from the load path.** It is still built on
**every** load, before the binary path can intervene.

## What actually happens on a load

`loaders/load_molsysmt.py:load_from_molsysmt`, in this order and
unconditionally:

1. `viewer_json = view._molsys.to_form("molsysmt.ViewerJSON")`
2. `payload = _serialize_molsys_payload(viewer_json, …)`
3. `view._send({"op": "load_molsys_payload", "payload": payload, …})`

Only in step 3 does `core.py:_try_send_array_native_molsys` intercept: it matches
on `op == "load_molsys_payload"`, re-serializes from `self._molsys` as typed
buffers, and streams those **instead**.

So the array-native path does not avoid the JSON work. **It avoids sending it.**
The payload is built in full and then discarded.

## Why it is built anyway — the reason is good

`_try_send_array_native_molsys` stores `"fallback": dict(message)` in the stream
state. If the stream is refused, times out (30 s), or the connector has no binary
transport, that retained JSON message is delivered instead. Roadmap gate 1
required a *behaviorally equivalent JSON fallback*, and this is how that promise
is kept.

The design is sound. What is wasteful is that the insurance is paid **eagerly**,
on every load, including the overwhelming majority where it is never claimed.

## The cost, measured

`pentalanine`, 62 atoms × 5,000 structures, after both July deep-copy fixes:

| | |
|---|---:|
| `to_form("molsysmt.ViewerJSON")` — JSON path only | **381 ms** |
| `serialize_array_native_molsys(molsys)` — binary path | **37 ms** |
| whole `view.load(molsys)` | 1,434 ms |

The JSON path costs **~10×** the binary one, and `to_form` is only its first
stage — `_serialize_molsys_payload` then rebuilds every column through
`np.asarray(...).tolist()` on top of it.

## The proposal

Make the fallback **lazy**: pass a thunk rather than a built payload.

- `load_from_molsysmt` decides whether binary is available *before* serializing
  (the capability is already known — `_binary_structure_transport_limit()`
  returns `None` when there is none).
- When binary is available, send a message carrying a *callable* that would
  produce the JSON payload, and let `_try_send_array_native_molsys` retain that
  callable as its fallback instead of a dict.
- `_fallback_binary_structure_stream` invokes it at the moment it is needed —
  which is a path that already tolerates being slow, because it is an error path.

Nothing about the fallback's *behaviour* changes; only when it is computed.

## What to be careful about

- **The fallback must still be reproducible at the moment it is claimed.** If the
  thunk closes over `self._molsys` and the system was replaced meanwhile, it
  would serialize the wrong generation. The stream already carries a
  `generation` counter for exactly this class of bug — the thunk must be bound to
  the same generation and refuse to run against a newer one.
- **The scale guard and the hierarchy queries** (`_safe_get_atom_attribute` for
  molecule/component indices and names) currently run in the same function.
  Decide deliberately which of those are needed for the binary path — the scale
  warning must still fire, since it is about memory the binary path also uses.
- **`n_structures` is derived from the payload** when MolSysMT does not report
  it (`len(payload.get("structures"))`). That fallback path must not force the
  payload to be built. It already reads `structures.n_structures` first.

## Acceptance

- On a negotiated-binary load, `to_form("molsysmt.ViewerJSON")` is **not
  called** — asserted by spying on it, not by timing.
- The JSON fallback still delivers a byte-identical payload when the stream is
  refused or times out, covered by the existing timeout tests.
- Mutation check: force the thunk to build eagerly and the "not called"
  assertion must fail.
- Re-run `devtools/benchmarks/startup_baseline.py`; `view.load` should drop by
  roughly the JSON path's share.
