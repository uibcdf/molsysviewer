---
summary: Box stroke width rejects length quantities and accepts invalid geometry.
issue: uibcdf/molsysviewer#327
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [api, box, units]
guard: tests/test_box_state_persistence.py
normative:
blocked_by: []
supersedes: []
---

# Physical width of the simulation-box display

The real three-structure pentalanine control accepts zero, negative, infinite
and NaN widths, but a scalar `quantity(0.2, "nm")` raises `DimensionalityError`.
The width digester admits and standardizes lengths; `show_box` then attempts a
dimensioned `float` conversion. This is Viewer display logic, not provider
science. The complete open/closed inventory was checked: #96 corrected cell
vectors and offsets, not stroke widths.

Under A5/#319, receive a scalar positive finite width before changing any
existing display. Keep bare scalar/default widths in angstrom and explicitly
convert length quantities at the renderer boundary, independently of the
session policy. Receive both ordinary and digestion-bypassed internal calls,
exact preserved prior state on invalid input, and #326's portable display
recipe. Scientific cells must remain unchanged.

**Resolved in source:** `show_box` validates positive finite scalar width before
changing any display and converts explicit lengths to angstrom through
PyUnitWizard. The guard `tests/test_box_state_persistence.py` receives bare,
nm and angstrom values under both nm/angstrom application policies, ordinary
and digestion-bypassed routes, rejected invalid widths and unchanged cells.
The before-fix width selection has eighteen genuine failures; all 61 current
box cases pass within the overlapping 551-case state/session boundary gate.
The complete Studio browser entry separately receives a 0.125 nm stroke as
1.25 angstrom on the actual restored twelve-edge mesh. See the
[bounded receipt](../box_display_receiving_20261107.json). These scopes do not
qualify installed packages or complete parent A5.
