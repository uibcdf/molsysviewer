
# ID vs Index in TopoMT

TopoMT distinguishes between **public identifiers** (`feature_id`) and
**internal numeric indexes** (`feature_index`).

- **`feature_id`** is the public, stable, human-readable identifier. It is the
  name that external code, serialized data, documentation, and users should
  refer to. IDs can carry semantics (e.g. `cavity_003`, `mouth_cavity_3`) and
  should remain stable across sessions and reloads.

- **`feature_index`** is the internal, numeric handle that the registry uses
  for fast lookups, ordering, and parent–child relations. Indexes are assigned
  at registration time if the feature does not provide one. They are optimized
  for in-memory operations, not for long-term persistence.

The **Topography** registry therefore keeps:
1. an internal store keyed by index: `index → feature`
2. an auxiliary mapping keyed by id: `id → index`

Public APIs (such as `link(child_id, parent_id)`, `children_of(feature_id)`, or
`parents_of(feature_id)`) accept **IDs**, because that is what users and
higher-level tools naturally work with. Internally, these IDs are immediately
resolved to indexes and all internal structures (dimension lists, shape lists,
type lists, parent–child graphs) operate on indexes.

This design combines the stability and readability of IDs with the efficiency
and coherence of index-based storage.
