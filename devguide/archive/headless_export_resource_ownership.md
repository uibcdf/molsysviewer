---
summary: Headless PNG export owns temporary HTML and HTTP server resources incorrectly
issue: uibcdf/molsysviewer#228
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: ['export', 'resources']
guard: tests/test_headless_export_resources.py
normative:
blocked_by: []
supersedes: []
---

# Headless PNG export owns temporary HTML and HTTP server resources incorrectly

**Reported:** 2026-10-10 during the authorized integrated resource-owner review, uibcdf/molsysviewer#200 and uibcdf/molsyssuite#104.

## What

The Playwright adapter writes scratch HTML inside the package and fails on read-only package directories. Its auxiliary HTTP server lacks explicit socket close and thread joining.

## How

Move scratch HTML into a managed directory, serve the package runtime through an explicit route, bind port zero, and close browser/thread/socket in finally.

## Why

This affects applicable development or public export/preview operations. Caller-owned outputs and retained scientific evidence must survive cleanup.

## What was refuted

A managed scratch lifetime does not authorize deleting caller output, unrelated historical directories, package files or another session's evidence. Initial diagnosis is source inspection; executed verification is recorded at closure.

## Executed diagnosis

The initial run established that the development environment lacked the optional
Python Playwright dependency. After installing Playwright 1.57.0, Chromium
reported `Could not create a WebGL rendering context`, followed by an exported
scene without a WebGL canvas. This was an executed rendering failure, not an
HTTP/path assumption. Explicit ANGLE/SwiftShader configuration now enables
headless software rendering; an early WebGL2 check reports unavailable contexts
instead of waiting silently for the exported scene. No Qt/GPU certification is
inferred from this software-rendered PNG.

## Resolution

All three headless-resource guards pass, including an actual nonuniform PNG from
an imported copy of the package whose directories are read-only. The real server
success/failure guards verify thread exit, socket fileno -1, deleted scratch and
preserved caller output. The single global Python run retains eight existing Qt context failures; the six integration bookkeeping failures are repaired in scoped verification. Reviewed integration and full core browser completion are retained in the review receipt.
