---
summary: Evaluate copying equivalent Python code from Studio.
issue: uibcdf/molsysviewer#226
status: open
opened: 2026-10-10
closed:
verification: inspected
area: [studio, api]
guard:
normative:
blocked_by: []
supersedes: []
---

## What
Evaluate a future Copy Python action for Studio operations so notebook users can reproduce graphical work through the public API. Diego explicitly defers this opportunity beyond the current pre-1.0 work.

## How
Study an owner-provided representation of accepted operations, safe quoting, quantities, atom/structure scope, names, defaults and backend-dependent capabilities. Define whether copying covers one operation or a reproducible scene workflow. Do not infer code by scraping UI labels or silently serialize credentials/server-only paths.

## Why
Studio and the API already share native owners. An explicit code bridge could improve reproducibility and learning, but needs a separate contract and design review. No implementation or 1.0 promise is included.
