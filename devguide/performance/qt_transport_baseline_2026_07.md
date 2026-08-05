# Qt standalone transport baseline — July 2026

## Decision

Binary transport is worth it on Qt, by a wide margin, and it does **not** need a
new channel: the existing `molsysviewer-payload` scheme handler already serves
arbitrary bytes from a `QBuffer`, and the only thing tying it to JSON is the
`application/json` content type in its `job.reply`.

Qt is in scope for 1.0 and had never been measured. This closes Phase 0 for the
Qt connector, the counterpart of
[`trajectory_transport_baseline_2026_07.md`](trajectory_transport_baseline_2026_07.md)
for AnyWidget, and feeds
[`data_plane_architecture.md`](../data_plane_architecture.md).

## Command

```bash
python devtools/benchmarks/qt_transport_baseline.py
```

## What Qt does today

For a molecular payload above `payload_ref_threshold_bytes`,
`_materialize_payload_ref` serializes it to JSON text, keeps those bytes
resident until the page asks for them, and rewrites the message to
`load_molsys_payload_ref` pointing at a `molsysviewer-payload://payload/<id>`
URL. The page fetches that URL and receives `application/json`.

## Measurements

| case | Qt JSON today | array-native | ratio |
|---|---|---|---|
| 62 atoms x 1,000 structures | 3.68 MB, 898 ms | 0.79 MB, 32 ms | 4.6x bytes, 28x prepare |
| 62 atoms x 5,000 structures | 18.37 MB, 4,293 ms | 3.95 MB, 36 ms | 4.7x bytes, 120x prepare |

Breakdown of the 4,293 ms: `ViewerJSON` 1,423 ms, nested-list normalization
2,130 ms, JSON encoding 739 ms.

## Reading

**Preparation dominates, not the wire.** The bytes shrink by a steady ~4.7x, but
the preparation advantage grows from 28x to 120x between the two cases, because
the array-native path stays flat (32 ms to 36 ms) while the JSON pipeline scales
with the number of structures.

In practice a standalone user waits **about 4.3 seconds of pure Python** before a
5,000-structure trajectory can even reach the window, on top of the Numba cold
start already described in
[`../standalone_performance_and_depythonization.md`](../standalone_performance_and_depythonization.md).
The two costs add up.

Most of this gain is not Qt-specific: it is the same `ViewerJSON` and
nested-list amplification already removed on AnyWidget by D1. Qt simply still
pays it in full.

## Why not QWebChannel

QWebChannel is Qt's official Python/JS bridge and was considered first. Its
transport is JSON by construction:

```
QWebChannelAbstractTransport.sendMessage(message: Dict[str, QJsonValue]) -> None
```

Every message is a `QJsonObject`, so a `QByteArray` crosses it base64-encoded
inside a JSON string. For the 3.95 MB case that means roughly 5.3 MB of JSON
text plus a decode pass on the browser side — reintroducing exactly the
text-encoding step D1 removed, to arrive at the same place.

It is the right tool for a different job: exposing a Python object to JS with
signals, slots and properties. It is the wrong one for shipping bulk arrays. It
would also add a *second* transport alongside a channel that already works, with
its own failure modes to keep in sync.

The scheme handler wins because it serves raw bytes with no encoding, the
frontend already uses `fetch`, and the transport diagnostic
([`../audits/standalone_qt_event_transport_diagnostic.md`](../audits/standalone_qt_event_transport_diagnostic.md))
already proved the scheme works with `fetch` in a real Qt window, with the flags
it needs (`SecureScheme`, `CorsEnabled`, `FetchApiAllowed`, `LocalScheme`).

## Not measured

Browser-side decoding and Mol\* construction inside a real Qt window need a
display with WebGL and are out of scope here. What is measured is the Python
side, which is where the 4.3 seconds are spent.
