---
summary: Scene-contracts test sends dynamic updates for a frame it never displays.
issue: uibcdf/molsysviewer#348
status: resolved
opened: 2026-11-10
closed: 2026-11-10
severity: medium
verification: reproduced
area: [tests, regions, trajectory]
guard: tests/test_scene_contracts_browser.py::test_dynamic_memberships_follow_native_frames_and_reject_stale_packets
normative:
blocked_by: []
supersedes: []
---

**Resolved in source — 2026-11-10:** the independent native-coordinate
selection gives populations 1 → 2 → 1 across real structures [0,8,3]. The browser
moves to each structure, checks exact indices and actual Molstar component
size/style, and proves that an old-frame packet cannot overwrite it. The
focused explicit guard and corrected six-suite continuation pass. No product
frame-isolation rule is relaxed. The original 45-pass/one-failure aggregate
remains failed; complete consolidated CI is a separate acceptance obligation.

The complete core campaign stops at suite 46 after 45 successful entries. Its
last scene-contracts scenario sends frame-1/2 dynamic updates to a controller
holding a single PDB structure at frame 0. The expected four atoms remain two
because the resolved #338 contract correctly refuses foreign-frame packets.
No product regression is established by that assertion.

Use real pentalanine structures [0,8,3], a bounded native geometric selection
checked against independent coordinates, and actual trajectory navigation.
Keep exact rendered populations, style preservation and explicit stale-frame
refusal. Preserve the original full-lane failure and do not relax the product's
frame isolation. Receiving the remaining six entries separately does not turn
the original failed aggregate into a passing full run.
