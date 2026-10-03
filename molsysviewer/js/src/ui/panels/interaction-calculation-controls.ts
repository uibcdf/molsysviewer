/** Studio scientific options. Blank fields delegate defaults to the named getter. */
export type ScientificValues = Record<string, string>;
export type ScientificControl = {
    key: string; label: string; type: "length" | "angle" | "angle-range" | "choice" | "names";
    required?: boolean; allowZero?: boolean; choices?: Array<[string, string]>;
};
export type CalculationCriterion = {
    key: string; label: string; parameters: Record<string, unknown>;
    controls: ScientificControl[]; chemistry: boolean; help: string;
};
const length = (key: string, label: string, required = false, allowZero = false): ScientificControl =>
    ({ key, label, type: "length", required, allowZero });
const angle = (label: string, required = false): ScientificControl =>
    ({ key: "angle_threshold", label, type: "angle", required });
const distance = length("distance_threshold", "Distance cutoff");
const offset = length("offset_threshold", "Lateral offset cutoff", false, true);
const planarity = length("planarity_threshold", "Maximum ring-plane deviation", true, true);
const ringGeometry: ScientificControl = { key: "geometry", label: "Ring geometry", type: "choice",
    choices: [["", "Both (method default)"], ["parallel", "Parallel"], ["edge_to_face", "Edge-to-face"]] };
const waterOrder: ScientificControl = { key: "order", label: "Number of mediator waters", type: "choice",
    choices: [["", "One water · two H-bond legs"], ["2", "Two waters · three H-bond legs"]] };
const modern = "Requires declared chemical connectivity and the chemistry used by this criterion.";

export function calculationCriteria(kind: string): CalculationCriterion[] {
    switch (kind) {
        case "hbond": return [
            { key: "buch", label: "Buch · H–acceptor distance", parameters: { method: "buch" },
                controls: [length("distance_threshold", "H–acceptor distance cutoff")], chemistry: false,
                help: "Distance-only criterion; no angular condition." },
            { key: "luzard_chandler", label: "Luzard–Chandler · distance and angle", parameters: { method: "luzard_chandler" },
                controls: [length("distance_threshold", "Donor–acceptor distance cutoff"), angle("Maximum H–donor–acceptor angle")],
                chemistry: false, help: "The angle is measured at the donor, unlike the D–H–A minimum below." },
            { key: "baker_hubbard", label: "Baker–Hubbard", parameters: { method: "baker_hubbard" },
                controls: [length("distance_threshold", "H–acceptor distance cutoff"), angle("Minimum donor–H–acceptor angle")],
                chemistry: true, help: modern },
            { key: "wernet_nilsson", label: "Wernet–Nilsson", parameters: { method: "wernet_nilsson" },
                controls: [length("distance_threshold", "Donor–acceptor distance intercept")], chemistry: true,
                help: `Uses a distance–angle curve; there is no independent angular cutoff. ${modern}` },
            ...["elemental_fon", "smarts_donor_acceptor"].map(profile => ({
                key: profile, label: `Donor–acceptor distance and angle · ${profile === "elemental_fon" ? "elemental F/O/N" : "SMARTS sites"}`,
                parameters: { method: "donor_acceptor_distance_angle", profile },
                controls: [length("distance_threshold", "Donor–acceptor distance cutoff"), angle("Minimum donor–H–acceptor angle")],
                chemistry: true, help: modern,
            })),
        ];
        case "disulfide_candidate": return [{ key: "default", label: "S–S geometric candidates", parameters: {}, chemistry: false,
            controls: [length("max_bond_length", "S–S distance cutoff"), { key: "group_names", label: "Residue names (comma-separated; blank = CYS)", type: "names" }],
            help: "Geometric candidates; calculation does not declare a covalent bond or change topology." }];
        case "ionic_contact": return [{ key: "default", label: "Minimum distance between charged groups", parameters: {}, chemistry: true,
            controls: [length("distance_threshold", "Minimum-atom distance cutoff", true)],
            help: `An explicit distance is required. Centroid guides retain the measured minimum-atom distance definition. ${modern}` }];
        case "pi_pi": return [
            { key: "three_atom_plane", label: "Centroid, angle and offset · three-atom planes", parameters: { method: "centroid_angle_offset", profile: "three_atom_plane" },
                controls: [distance, angle("Maximum deviation from parallel/perpendicular"), offset, ringGeometry], chemistry: true, help: modern },
            { key: "least_squares", label: "Centroid, angle and offset · fitted planes", parameters: { method: "centroid_angle_offset", profile: "least_squares" },
                controls: [length("distance_threshold", "Centroid distance cutoff", true), angle("Maximum deviation from parallel/perpendicular", true),
                    { ...offset, required: true }, planarity, ringGeometry], chemistry: true,
                help: `This criterion requires explicit distance, angle, offset and planarity limits. ${modern}` },
            ...["smarts_5_6", "aromatic_cycles"].map(profile => ({ key: profile,
                label: `Plane angle and intersection · ${profile === "smarts_5_6" ? "SMARTS 5/6-member rings" : "aromatic cycles"}`,
                parameters: { method: "plane_angle_intersection", profile }, controls: [distance, ringGeometry], chemistry: true,
                help: `The profile fixes angular intervals and plane-intersection rules. ${modern}` })),
        ];
        case "cation_pi": return [
            { key: "smarts_5_6", label: "Centroid distance and angle · SMARTS rings", parameters: { method: "centroid_distance_angle", profile: "smarts_5_6" },
                controls: [distance, angle("Maximum displacement–ring-normal angle")], chemistry: true, help: modern },
            { key: "three_atom_plane", label: "Centroid distance and offset · three-atom plane", parameters: { method: "centroid_distance_offset", profile: "three_atom_plane" },
                controls: [distance, offset], chemistry: true, help: `This criterion has no angular filter. ${modern}` },
            { key: "least_squares", label: "Centroid, angle and offset · fitted plane", parameters: { method: "centroid_angle_offset", profile: "least_squares" },
                controls: [length("distance_threshold", "Centroid distance cutoff", true), angle("Maximum displacement–ring-normal angle", true),
                    { ...offset, required: true }, planarity], chemistry: true,
                help: `This criterion requires explicit distance, angle, offset and planarity limits. ${modern}` },
        ];
        case "halogen_bond": return [{ key: "default", label: "Distance and two angular intervals", parameters: {}, chemistry: true,
            controls: [length("distance_threshold", "Halogen–acceptor distance cutoff"),
                { key: "donor_angle_range", label: "Donor–halogen–acceptor angle interval", type: "angle-range" },
                { key: "acceptor_angle_range", label: "Halogen–acceptor–reference angle interval", type: "angle-range" }], help: modern }];
        case "hydrophobic_contact": return [{ key: "default", label: "Hydrophobic atom-pair distance", parameters: {}, chemistry: true,
            controls: [distance], help: modern }];
        case "metal_coordination_candidate": return [{ key: "default", label: "Metal–ligand distance candidates", parameters: {}, chemistry: true,
            controls: [length("distance_threshold", "Metal–ligand distance cutoff")],
            help: `Geometric candidates; topology is unchanged. ${modern}` }];
        case "water_bridge": return ["baker_hubbard", "wernet_nilsson", "elemental_fon", "smarts_donor_acceptor"].map(key => ({
            key, label: `Water-path H-bonds · ${key === "baker_hubbard" ? "Baker–Hubbard" : key === "wernet_nilsson" ? "Wernet–Nilsson" : key === "elemental_fon" ? "donor–acceptor, elemental F/O/N" : "donor–acceptor, SMARTS"}`,
            parameters: { hbond_method: ["elemental_fon", "smarts_donor_acceptor"].includes(key) ? "donor_acceptor_distance_angle" : key,
                ...(["elemental_fon", "smarts_donor_acceptor"].includes(key) ? { hbond_profile: key } : {}) },
            controls: [waterOrder, distance,
                ...(key === "wernet_nilsson" ? [] : [angle("Minimum donor–H–acceptor angle for each leg")])],
            chemistry: true, help: `One occurrence retains every directed H-bond leg. ${key === "wernet_nilsson" ? "The leg criterion uses its distance–angle curve. " : ""}${modern}`,
        }));
        default: return [];
    }
}

export function initialCalculationCriterion(kind: string, defaults: Record<string, unknown> = {}): string {
    const criteria = calculationCriteria(kind);
    return (criteria.find(item => Object.entries(defaults).every(([key, value]) => item.parameters[key] === value)) ?? criteria[0])?.key ?? "";
}

function finiteNumber(text: string, label: string): number {
    const value = Number(text);
    if (!text.trim() || !Number.isFinite(value)) throw new Error(`${label}: enter a finite number.`);
    return value;
}
function unitFor(control: ScientificControl, values: ScientificValues): string {
    const unit = values[`${control.key}-unit`] || (control.type === "length" ? "nm" : "degrees");
    const allowed = control.type === "length" ? ["nm", "angstroms"] : ["degrees", "radians"];
    if (!allowed.includes(unit)) throw new Error(`${control.label}: unsupported unit.`);
    return unit;
}
function angleValue(text: string, unit: string, label: string): number {
    const value = finiteNumber(text, label);
    if (value < 0 || value > (unit === "degrees" ? 180 : Math.PI)) throw new Error(`${label}: angle must be between 0 and 180 degrees.`);
    return value;
}

/** Build only controls belonging to the selected criterion; never carry hidden fields. */
export function scientificParameters(kind: string, key: string, values: ScientificValues): Record<string, unknown> {
    const criterion = calculationCriteria(kind).find(item => item.key === key);
    if (!criterion) throw new Error("Select an available interaction criterion.");
    const parameters = { ...criterion.parameters };
    for (const control of criterion.controls) {
        const text = (values[control.key] || "").trim();
        if (control.type === "angle-range") {
            const low = (values[`${control.key}-min`] || "").trim(), high = (values[`${control.key}-max`] || "").trim();
            if (!low && !high) continue;
            const unit = unitFor(control, values);
            if (angleValue(low, unit, control.label) > angleValue(high, unit, control.label)) throw new Error(`${control.label}: minimum must not exceed maximum.`);
            parameters[control.key] = [`${low} ${unit}`, `${high} ${unit}`];
        } else if (!text) {
            if (control.required) throw new Error(`${control.label} is required for this criterion.`);
        } else if (control.type === "length" || control.type === "angle") {
            const unit = unitFor(control, values);
            const value = control.type === "angle" ? angleValue(text, unit, control.label) : finiteNumber(text, control.label);
            if (control.type === "length" && (value < 0 || (!control.allowZero && value === 0))) throw new Error(`${control.label}: enter a ${control.allowZero ? "nonnegative" : "positive"} length.`);
            parameters[control.key] = `${text} ${unit}`;
        } else if (control.type === "choice") {
            if (!control.choices?.some(([key]) => key === text)) throw new Error(`${control.label}: select an available value.`);
            parameters[control.key] = control.key === "order" ? Number(text) : text;
        } else {
            const names = text.split(",").map(name => name.trim());
            if (names.some(name => !name)) throw new Error(`${control.label}: use comma-separated names without empty entries.`);
            parameters[control.key] = names;
        }
    }
    return parameters;
}

/** Changing a display unit keeps already-entered physical cutoffs unchanged. */
export function changeScientificUnit(values: ScientificValues, control: ScientificControl, next: string): void {
    const previous = unitFor(control, values);
    const allowed = control.type === "length" ? ["nm", "angstroms"] : ["degrees", "radians"];
    if (!allowed.includes(next)) throw new Error("Unsupported scientific control unit.");
    const scale = control.type === "length" ? (previous === "nm" ? 10 : 0.1) : (previous === "degrees" ? Math.PI / 180 : 180 / Math.PI);
    if (previous !== next) for (const key of control.type === "angle-range" ? [`${control.key}-min`, `${control.key}-max`] : [control.key]) {
        if (values[key]?.trim() && Number.isFinite(Number(values[key]))) values[key] = String(Number(values[key]) * scale);
    }
    values[`${control.key}-unit`] = next;
}
