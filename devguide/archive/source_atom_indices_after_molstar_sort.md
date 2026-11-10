---
summary: Preserve source atom identities across Molstar internal row sorting.
issue: uibcdf/molsysviewer#347
status: resolved
opened: 2026-11-10
closed: 2026-11-10
severity: high
verification: reproduced
area: [selection, scientific-identity, rendering]
guard: tests/test_source_atom_indices.py::test_real_source_atom_correspondence_and_recovered_geometry
normative:
blocked_by: []
supersedes: []
---

**Resolved in source — 2026-11-10:** real pentalanine canonical/permuted
orders, three structures and recovered scenes pass the explicit browser guard;
actual native Qt and Jupyter/both-popup receiving pass the strict original
source-index boundary. The lazy map does not copy the trajectory. The complete
core attempt receives 45 suites, then fails on the unrelated outdated test
#348; the corrected final six pass separately. The original failed aggregate
is retained and is not presented as a green consolidated/hosted run. Runtime
changes are source-received; installed, consolidated and human acceptance keep
their separate scope. The closing GitHub comment names the delivered commit.

The source/native atom axis and Molstar's grouped model-element axis differ for
noncontiguous group membership. Actual Qt receiving on c60482de observes map
`[0,2,3,1,4,5]`; requesting source atom 1 selects source atom 2. Native detector
results and rendered coordinates are correct when read through that map. This
is a Viewer boundary defect, not a Molstar sorting defect or a coordinate error.

The independent water fixture uses a public RDKit-to-MolSys conversion with
explicit coordinates. An additional regression must exercise canonical extraction and an explicitly declared public atom permutation
of the real pentalanine demo. Never reorder the fixture to hide the permutation.

The repair keeps protocol/Python indices as source positions. Translate model
locations for picking, metadata, group strips, regions, colors, annotations,
measures and atom-based shapes. Native label group/chain axes apply only when
explicit index columns were supplied; retain legacy author-label behavior.
Molstar already applies its source map to coordinates and stored index-pair
bonds; do not remap either twice. Existing partial coordinate edits also use
Molstar's inverse and retain their separate scientific invalidation contract.

A lazy inverse cache belongs to the shared atomic hierarchy, not each trajectory
frame. Do not create an atom-by-structure map or copy a trajectory for selection.
Receive actual identity/geometry and source lifetime, with contiguous and
nonidentity inputs, multiple structures and both popup boundaries. Source fixes,
full core checks, native Qt and postponed human/installed acceptance remain
separate. D6.9 and E1 are not credited while this defect prevents their receiving.

Private controlled records 86/87/88 under the November robustness campaign
retain original failures and unchanged input inventories. 86 also includes an
independent Jupyter driver error (filling a deliberately hidden control); its
repair is not evidence that the native identity error is fixed. 88 normalizes
coordinate inspection using Molstar's public source map, then independently
fails its strict source-atom selection assertion. No source result is promoted
from that coordinate-helper correction alone.

Source receiving 104 now passes the real-browser guard: both atom orders,
three structure observations each, original and recovered scenes. The strict
single-atom identity, complete picked source group, source-indexed region and
colors, atomic/centroid measures, ordinary labels, callouts, and static versus
explicitly structure-indexed spheres are retained. Native coordinate/map
assertions use the public permutation report. This does not yet close the issue:
covering core receiving and the original native Qt control remain pending.

Earlier observer/fixture failures are retained. The corrections respect native
extraction's canonical source order, native label bounding-sphere placement,
context-menu group expansion, OrderedSet interval encoding and static shape
lifetime. None changes the molecular fixture into a convenient contiguous input,
removes the nonidentity assertion or changes a scientific/visual definition.
See the source/rendering-index contract in
`docs/content/developer/protocol_and_payloads.md`.
