---
summary: Studio catalogue source decoding fails under Windows cp1252
issue: uibcdf/molsysviewer#205
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [testing, studio]
guard: tests/test_studio_shape_examples.py
normative:
blocked_by: []
supersedes: []
---

# Studio catalogue decoding fails under Windows cp1252

**Reported:** 2026-10-10, review of exact-source pair run 38031216855 on 4ca5a248.

## What

Windows job 114152375180 fails collection at test_studio_shape_examples.py:15.
The default cp1252 decoder cannot read byte 0x81 in the UTF-8 TypeScript source.
Reading the actual source explicitly as cp1252 reproduces the UnicodeDecodeError.

## How

The module-level catalogue extraction uses Path.read_text() without an encoding.
The fixture contains Unicode icons and the owned source is UTF-8.

## Why

All nine displayed catalogue examples must execute consistently on every
supported platform. This is test-source decoding, not a geometry/API defect.

## What was refuted

The previous run remains globally failed; Linux/macOS success does not qualify
Windows. The compact log says two collection errors and identifies this location;
a fresh hosted collection is needed to exclude any remaining independent error.
The historical PNG timeout is separate and its original cause is not established.

## Resolution

Read the owned TypeScript source explicitly as UTF-8. The guard's module-level
extraction remains the same operation that failed on Windows, and it executes
all nine real shape examples. Local 10/10 cases pass in the explicit Python 3.14
development environment. Windows hosted qualification remains pending on the new
source; no historical run is relabelled as passing.
