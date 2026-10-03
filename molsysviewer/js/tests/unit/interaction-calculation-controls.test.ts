import assert from "node:assert/strict";
import test from "node:test";
import { calculationCriteria, initialCalculationCriterion, scientificParameters, changeScientificUnit }
    from "../../src/ui/panels/interaction-calculation-controls";

test("blank cutoffs delegate to named criteria without inventing numeric defaults", () => {
    assert.deepEqual(scientificParameters("hbond", "buch", {}), { method: "buch" });
    assert.deepEqual(scientificParameters("hbond", "luzard_chandler", {}), { method: "luzard_chandler" });
    assert.equal(initialCalculationCriterion("pi_pi", { profile: "three_atom_plane" }), "three_atom_plane");
    assert.deepEqual(scientificParameters("disulfide_candidate", "default", {}), {});
});

test("criterion changes cannot leak hidden scientific parameters", () => {
    const values = { distance_threshold: "0.4", angle_threshold: "120", profile: "explicit_sites", planarity_threshold: "0.1" };
    assert.deepEqual(scientificParameters("hbond", "wernet_nilsson", values), { method: "wernet_nilsson", distance_threshold: "0.4 nm" });
    assert.deepEqual(scientificParameters("cation_pi", "three_atom_plane", values), {
        method: "centroid_distance_offset", profile: "three_atom_plane", distance_threshold: "0.4 nm",
    });
});

test("ionic and fitted-plane criteria require their scientific limits", () => {
    assert.throws(() => scientificParameters("ionic_contact", "default", {}), /required/);
    assert.throws(() => scientificParameters("pi_pi", "least_squares", { distance_threshold: "0.5" }), /required/);
    assert.deepEqual(scientificParameters("pi_pi", "least_squares", {
        distance_threshold: "0.5", angle_threshold: "30", offset_threshold: "0", planarity_threshold: "0",
    }), { method: "centroid_angle_offset", profile: "least_squares", distance_threshold: "0.5 nm",
        angle_threshold: "30 degrees", offset_threshold: "0 nm", planarity_threshold: "0 nm" });
});

test("angular intervals cross the boundary as two quantities with explicit units", () => {
    assert.deepEqual(scientificParameters("halogen_bond", "default", {
        "donor_angle_range-min": "130", "donor_angle_range-max": "180",
        "acceptor_angle_range-min": "1", "acceptor_angle_range-max": "2", "acceptor_angle_range-unit": "radians",
    }), { donor_angle_range: ["130 degrees", "180 degrees"], acceptor_angle_range: ["1 radians", "2 radians"] });
    for (const values of [
        { "donor_angle_range-min": "130" },
        { "donor_angle_range-min": "180", "donor_angle_range-max": "130" },
        { "donor_angle_range-min": "0", "donor_angle_range-max": "181" },
    ]) assert.throws(() => scientificParameters("halogen_bond", "default", values));
});

test("unit changes conserve the physical cutoff and keep empty defaults empty", () => {
    const control = calculationCriteria("hbond")[0].controls[0];
    const values = { distance_threshold: "0.4" };
    changeScientificUnit(values, control, "angstroms");
    assert.equal(values.distance_threshold, "4");
    assert.equal(scientificParameters("hbond", "buch", values).distance_threshold, "4 angstroms");
    const range = calculationCriteria("halogen_bond")[0].controls[1];
    const angles = { "donor_angle_range-min": "0", "donor_angle_range-max": "180" };
    changeScientificUnit(angles, range, "radians");
    assert.deepEqual(scientificParameters("halogen_bond", "default", angles).donor_angle_range, ["0 radians", `${Math.PI} radians`]);
    const empty = {};
    changeScientificUnit(empty, control, "angstroms");
    assert.deepEqual(scientificParameters("hbond", "buch", empty), { method: "buch" });
});

test("invalid numbers, units and choices fail before dispatch", () => {
    for (const distance_threshold of ["NaN", "Infinity", "-1", "0"]) {
        assert.throws(() => scientificParameters("hbond", "buch", { distance_threshold }));
    }
    assert.throws(() => scientificParameters("hbond", "buch", { distance_threshold: "1", "distance_threshold-unit": "degrees" }));
    assert.throws(() => scientificParameters("water_bridge", "baker_hubbard", { order: "3" }));
    assert.throws(() => scientificParameters("disulfide_candidate", "default", { group_names: "CYS,,CYX" }));
    assert.deepEqual(scientificParameters("disulfide_candidate", "default", { group_names: "CYS, CYX" }), { group_names: ["CYS", "CYX"] });
});

test("water order remains an integer and Wernet–Nilsson legs have no scalar angular override", () => {
    assert.deepEqual(scientificParameters("water_bridge", "wernet_nilsson", { order: "2", angle_threshold: "90" }), {
        hbond_method: "wernet_nilsson", order: 2,
    });
    assert.deepEqual(scientificParameters("water_bridge", "smarts_donor_acceptor", {}), {
        hbond_method: "donor_acceptor_distance_angle", hbond_profile: "smarts_donor_acceptor",
    });
});

for (const kind of ["hbond", "disulfide_candidate", "ionic_contact", "pi_pi", "cation_pi", "halogen_bond",
    "hydrophobic_contact", "metal_coordination_candidate", "water_bridge"]) {
    test(`${kind}: every offered criterion has valid independently staged controls`, () => {
        for (const criterion of calculationCriteria(kind)) {
            const values: Record<string, string> = {};
            for (const control of criterion.controls) if (control.required) values[control.key] = control.type === "angle" ? "30" : "0.4";
            assert.ok(scientificParameters(kind, criterion.key, values));
        }
    });
}
