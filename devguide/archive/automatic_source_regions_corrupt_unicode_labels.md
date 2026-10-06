---
summary: Automatic source regions corrupt Unicode labels shown in Studio
issue: uibcdf/molsysviewer#165
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: low
verification: reproduced
area: [loading, regions, ui]
guard: tests/test_load_usability.py::test_source_region_labels_preserve_unicode_and_identity
normative:
blocked_by: []
supersedes: []
---

# Automatic source regions corrupt Unicode labels shown in Studio

**Reported:** 2026-10-06 by Diego during the remote-Jupyter human review.
Source inspection and direct execution of the existing slug method reproduce
the strings; no automated card-rendering reproduction has been added.

## What

Progressive loading of bundled 1VII and caffeine with `label="Proteína"`
and `label="Cafeína"` creates Regions cards named `Prote_na` and `Cafe_na`.
The replaced character is the accented `í`; `_na` has no molecular meaning.
The original source labels remain in load records, and both sources and Whole
are reported present and correctly drawn.

## How

`molsysviewer/viewer/load.py::_load_region_base_tag` obtains the source label
and calls `RegionsMixin._slugify_region_tag`. Its expression
`re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_")` replaces accented
characters. Direct calls in `molsyssuite@uibcdf_3.14` return `Prote_na` and
`Cafe_na`. `js/src/ui/panels/regions-panel.ts` displays `item.tag` as card text.

Keep readable source names in the public card and specify their relationship
to Python lookup tags through the existing identity owner. Explicit tags
already permit Unicode through `TagManager._normalize`; determine whether
preserving automatic Unicode tags suffices before adding another naming field.
Retain unique tags, source IDs and region UIDs. Do not automatically retag
existing saved sessions or handles.

## Why

The public `label` argument and its automatic source regions (#151) should
identify the user's source with a comprehensible name. The lossy conversion
leaks into Studio and into Python tags. Cover accented/Unicode labels,
duplicate names, batch/progressive parity, rename, session round-trip and real
Studio rendering/actions when implementing the correction.

## What was refuted

This is not a special molecular suffix, a missing atom selection or lost
scientific source identity. It is a lossy automatic naming rule. General
Unicode rendering has not been shown to fail; the string is already corrupted
before it reaches the frontend. The direct probe initially used the incorrect
class name `RegionMixin`; reading the actual declaration and using
`RegionsMixin` reproduced the conversion.

## Resolution

Resolved on 2026-10-06. Automatic
load-source tags use the trimmed readable source label. The existing tag
registry and collision owner remain responsible for uniqueness; a duplicate
`Cafeína` becomes `Cafeína__2`. Other region-building recipes retain their
existing rules. No new naming field or session migration is introduced.

`tests/test_load_usability.py::test_source_region_labels_preserve_unicode_and_identity`
asserts exact accented, decomposed-accent and CJK tags for both batch and
progressive loading, source atom ranges, rename/UID continuity and MSV
round-trip. The companion test retains existing ASCII tags and their source
records when adding a Unicode-named source to a reopened session. All four
module cases pass.

The real Chromium composite-load guard opens Studio Regions, reads the actual
card text (including a duplicate suffix), and applies hide/show using the
Unicode tag against real Mol* transparency masks. Existing composite checks
also retain reopened and extracted source scenes. Human confirmation after
restarting the notebook kernel and refreshing the runtime is still pending.
The old source handoff is preserved at its original SHA. #166 separately
tracks an existing unit DOM fixture incompatibility, without changing naming
or browser runtime behavior.

The complete real-browser lane passes **39/39 core suites**. The once-run
Python suite returns 2,816 passed, 22 sandbox permission failures and 23
skipped in 524.08 s; normal pytest outside the sandbox passes the explicit
22 failed nodes. This selected follow-up is not a second complete run.
Environment, tested source hashes and validation limits are retained in
`devguide/load_usability_fixes_20261006.json`.
