---
summary: Studio Export reports incorrect image dimensions and saves HTML on the Python host
issue: uibcdf/molsysviewer#181
status: resolved
opened: 2026-10-09
closed: 2026-10-09
severity: medium
verification: reproduced
area: [studio, export]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Studio Export reports incorrect image dimensions and saves HTML on the Python host

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

The real drawing buffer was 1050 × 760 px: Studio announced 3840 × 2160 at scale 2, while the downloaded PNG was 2100 × 1520. On a standard Jupyter widget, export_html writes molsysviewer_export.html on the Python host instead of delivering the promised browser download.

## How

Use renderer dimensions for the image summary and reuse the Python HTML exporter to deliver the file to the requesting frontend. Keep public file export and remote delivery contracts intact.

The review also found that the transparency checkbox was represented by the
list of available publication variants, while Python ignored the requested
transparency. A separate `figure_background` projection now carries the actual
recipe background; variants keep their existing catalogue meaning.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

PNG summary now follows the actual renderer buffer and scale; figure_background carries the real recipe background. HTML uses the existing self-contained exporter and a request-specific transient browser reply, excluded from popup replay storage. The real-browser guard reads PNG dimensions/alpha and saved HTML bytes, and asserts that a duplicate reply produces only one download. Python export guards cover the same native delivery boundary.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.
