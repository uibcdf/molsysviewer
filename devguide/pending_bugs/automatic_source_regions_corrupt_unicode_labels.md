---
summary: Automatic source regions corrupt Unicode labels shown in Studio
issue: uibcdf/molsysviewer#165
status: open
opened: 2026-10-06
closed:
severity: low
verification: reproduced
area: [loading, regions, ui]
guard:
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

Pending. No runtime edit is made during the human review. Preserve the fixed
source handoff to MolSysMT while collecting the remaining observations.
