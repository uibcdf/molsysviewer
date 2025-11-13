# TopoMT — Feature Catalog

## 2D — `Feature2D` (shape features)

### Concavity — `shape_type = concavity`

Included:

| 2D Feature         | Dim | Geometric role              | Applicable Boundaries (1D)            | Applicable Points (0D) | Biological / Pharmacological Interpretation |
|--------------------|-----|-----------------------------|---------------------------------------|------------------------|--------------------------------------------|
| Cavity             | 2   | General concavity           | Mouth, Neck, Furrow, Funnel, EdgeLoop | Pit, Nadir             | Ligand or peptide binding regions, active/allosteric sites. |
| Void               | 2   | Internal cavity not exposed | Neck, Furrow                          | Pit                    | Cryptic pockets. |
| Pocket             | 2   | Closed concavity            | Mouth, Neck, Furrow, EdgeLoop         | Pit, Nadir             | Classic drug design target. |
| Channel            | 2   | Continuous channel          | Mouth, Neck                           | Pit                    | Ion/molecule transport; gating. |
| BranchedChannel    | 2   | Branched channel            | Mouth, Neck, BranchLine               | Pit, Bifurcation       | Multisite selectivity. |
| Groove             | 2   | Open elongated groove       | Mouth, Furrow                         | Pit                    | PPI and nucleic acid binding. |

To be considered for future inclusion:

| 2D Feature     | Dim | Geometric role                             | Applicable Boundaries (1D) | Applicable Points (0D) | Biological / Pharmacological Interpretation |
|----------------|-----|--------------------------------------------|----------------------------|------------------------|--------------------------------------------|
| Cleft          | 2   | Broad groove with opening gradient         | Mouth, Neck, Furrow        | Pit                    | Partial anchoring and functionalization. |
| Funnel         | 2   | Conical or narrowing entrance              | Mouth, Neck, EdgeLoop      | Pit                    | Geometric gating, access modulation. |
| Vestibule      | 2   | Pre-chamber near mouth of a pocket/channel | Mouth, Neck                | Pit                    | Selectivity filter. |
| Ampulla        | 2   | Bulbous widening along a channel           | Neck, BranchLine           | Pit, Bifurcation       | Stepwise occupancy, transport checkpoints. |
| Niche / Alcove | 2   | Lateral shallow recess                     | Neck, Furrow               | Pit                    | Anchoring sites for fragments or water networks. |

### Convexity — `shape_type = convexity`

Included:

| 2D Feature            | Dim | Geometric role                       | Applicable Boundaries (1D) | Applicable Points (0D) | Biological / Pharmacological Interpretation |
|-----------------------|-----|--------------------------------------|----------------------------|-------------------------|--------------------------------------------|
| Vexity                | 2   | General convex surface               | BaseRim, Neck, Ridge       | Apex                    | Shape complementarity in PPI. |
| Protrusion            | 2   | Defined bump                         | BaseRim, Neck, Ridge       | Apex                    | Epitopes / protruding recognition sites. |
| Dome                  | 2   | Hemispherical surface                | BaseRim, Ridge             | Apex                    | Protein–protein interfaces. |
| Spine                 | 2   | Elongated convex crest               | BaseRim, Ridge, Neck       | Apex                    | Anchoring or adhesion. |

To be considered for future inclusion:

| 2D Feature  | Dim | Geometric role                      | Applicable Boundaries (1D) | Applicable Points (0D) | Biological / Pharmacological Interpretation |
|-------------|-----|-------------------------------------|----------------------------|------------------------|--------------------------------------------|
| Bulge       | 2   | Localized rounded convexity         | BaseRim, Neck              | Apex                   | Epitope or recognition site. |
| RidgeCap    | 2   | Rounded top of a ridge              | BaseRim, Ridge             | Apex                   | Structural stabilization. |
| Knob / Boss | 2   | Small rounded bump                  | BaseRim, Ridge             | Apex                   | Local contact enhancement. |
| Buttress    | 2   | Flared base of a protrusion or dome | BaseRim, Ridge             | Apex                   | Structural support, shape modulation. |
| Pinnacle    | 2   | Narrow tall convexity               | BaseRim, Ridge             | Apex                   | Salient epitopes, targeted recognition. |

### Mixed — `shape_type = mixed`
| 2D Feature        | Dim | Geometric role                          | Applicable Boundaries (1D) | Applicable Points (0D) | Biological / Pharmacological Interpretation |
|-------------------|-----|-----------------------------------------|----------------------------|------------------------|--------------------------------------------|
| Interface         | 2   | Contact zone between structural domains | Seam, Isthmus, HingeLine   | —                      | PPI, protein–ligand, protein–membrane interfaces. |
| Patch             | 2   | Flat or irregular patch                 | Seam                       | —                      | Transient docking site. |
| Joint             | 2   | Structural articulation or transition   | Seam                       | —                      | Conformational switches. |

To be considered for future inclusion:

| 2D Feature   | Dim | Geometric role                           | Applicable Boundaries (1D) | Applicable Points (0D) | Biological / Pharmacological Interpretation |
|--------------|-----|------------------------------------------|----------------------------|------------------------|--------------------------------------------|
| Saddle       | 2   | Patch with negative Gaussian curvature   | Seam, HingeLine            | SaddlePoint            | Mechanical leverage zone, hinge geometry. |
| Trench       | 2   | Long shallow depression across interface | Seam                       | SaddlePoint            | Guiding grooves at contact regions. |

---

## 1D — `Feature1D` (boundaries)

> `shape_type = boundary`. Boundaries are associated to compatible Feature2Ds.

| 1D Boundary  | Dim | Applies to shape types      | Geometric role / topology                                      | Typical Biological / Pharmacological Use |
|--------------|-----|-----------------------------|----------------------------------------------------------------|------------------------------------------|
| Mouth        | 1   | concavity                   | Opening of a cavity                                            | Gating, accessibility, selectivity. |
| BaseRim      | 1   | convexity                   | Basal rim of convex features                                   | Structural support. |
| Neck         | 1   | concavity, convexity        | Narrowing transition                                           | Flow regulation, selectivity. |
| Ridge        | 1   | convexity                   | Convex crest boundary                                          | Anchoring line. |
| Furrow       | 1   | concavity                   | Internal axis line in grooves/clefts                           | Pharmacophore scaffolding. |
| Lip          | 1   | concavity, convexity, mixed | Flexible/dynamic boundary (cryptic sites)                      | Cryptic site modeling. |
| Seam         | 1   | mixed                       | Contact boundary between interface patches or mixed interfaces | Interface articulation. |
| Isthmus      | 1   | mixed, concavity, convexity | Bridge connecting two patches                                  | Bivalent ligand bridging, pathway connection. |
| EdgeLoop     | 1   | concavity                   | Closed boundary loop                                           | Loop perimeter analysis. |
| BranchLine   | 1   | concavity, mixed            | Line terminating at bifurcation                                | Channel branching. |
| HingeLine    | 1   | mixed                       | Curve concentrating relative motion                            | Hinge and lever geometry. |

---

## 0D — `Feature0D` (points)

> `shape_type = point`. Points are anchored to compatible Feature2Ds.

| 0D Point     | Dim | Applies to shape types         | Geometric role                                | Typical Biological / Pharmacological Use |
|--------------|-----|-------------------------------|-----------------------------------------------|------------------------------------------|
| Pit          | 0   | concavity                     | Local minimum of concavity                    | Hotspot candidate, anchor site. |
| Nadir        | 0   | concavity                     | Global minimum of a concavity                 | Key anchoring site. |
| Apex         | 0   | convexity                     | Local maximum of convexity                    | Epitope candidate. |
| Summit       | 0	 | convexity                     | Global maximum of a convexity (highest point) | Salient epitope apex, prime anchor for binder design
| Bifurcation  | 0   | concavity, mixed              | Junction point of branching pathways          | Transport path topology. |
| SaddlePoint  | 0   | mixed                         | Point of zero mean curvature in saddle patch  | Mechanical leverage point. |
| RidgeTip     | 0   | convexity                     | Tip along a ridge                             | Protrusive epitope geometry. |


---
