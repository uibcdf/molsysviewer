"""Viewer adapters for explicitly supported public MolSysMT interaction families."""

FAMILIES = {
    "hbond": ("hbonds", "get_hbonds", "Hydrogen bonds", {"method": "buch"}),
    "disulfide_candidate": ("disulfides", "get_disulfide_candidates", "Disulfide candidates", {}),
    "ionic_contact": ("ionic", "get_ionic_interactions", "Ionic contacts", {}),
    "pi_pi": ("pi_pi", "get_pi_pi_interactions", "Pi–pi interactions", {"profile": "three_atom_plane"}),
    "cation_pi": ("cation_pi", "get_cation_pi_interactions", "Cation–pi interactions", {}),
    "halogen_bond": ("halogen_bonds", "get_halogen_bonds", "Halogen bonds", {}),
    "hydrophobic_contact": ("hydrophobic", "get_hydrophobic_interactions", "Hydrophobic contacts", {}),
    "metal_coordination_candidate": (
        "metal_coordination",
        "get_metal_coordination",
        "Metal coordination candidates",
        {},
    ),
    "water_bridge": ("water_bridges", "get_water_bridges", "Water-mediated hydrogen bonds", {}),
}

PAIR_ROLES = {
    "hbond": ("hydrogen", "acceptor"),
    "ionic_contact": ("positive", "negative"),
    "pi_pi": ("ring_a", "ring_b"),
    "cation_pi": ("cation", "ring"),
    "halogen_bond": ("halogen", "acceptor"),
    "hydrophobic_contact": ("hydrophobic_1", "hydrophobic_2"),
    "metal_coordination_candidate": ("metal", "ligand"),
}


def segments(kind, participants):
    """Return display endpoint indices; preserve all scientific participants."""
    if kind == "disulfide_candidate":
        return [(0, 1)] if len(participants) == 2 else None
    roles = {p["role"]: i for i, p in enumerate(participants)}
    if len(roles) != len(participants):
        return None
    if kind == "water_bridge":
        legs = len(participants) // 3
        wanted = {f"leg_{leg}_{role}" for leg in range(1, legs + 1) for role in ("donor", "hydrogen", "acceptor")}
        if legs not in (2, 3) or set(roles) != wanted:
            return None
        return [(roles[f"leg_{leg}_hydrogen"], roles[f"leg_{leg}_acceptor"]) for leg in range(1, legs + 1)]
    pair = PAIR_ROLES.get(kind)
    wanted = (
        {"donor", "hydrogen", "acceptor"}
        if kind == "hbond"
        else ({"donor", "halogen", "acceptor", "acceptor_reference"} if kind == "halogen_bond" else set(pair or ()))
    )
    if pair is None or set(roles) != wanted:
        return None
    return [(roles[pair[0]], roles[pair[1]])]
