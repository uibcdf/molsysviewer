import assert from "node:assert/strict";
import { setImmediate } from "node:timers/promises";
import { Column, Table } from "molstar/lib/mol-data/db";
import { BasicSchema, createBasic } from "molstar/lib/mol-model-formats/structure/basic/schema";
import { getChemicalComponentMap, getSaccharideComponentMap } from "molstar/lib/mol-model-formats/structure/basic/properties";

// Real native tables and readers; the build-time cache repair is the only
// difference between the positive and original-provider controls.
function visit(index, category = "absent", authOnly = false) {
    const xyz = new Float32Array([0, 1, 2, 3, 4, 5, 6, 7, 8]);
    const names = Column.ofStringArray(["ALA", "NAG", "HOH"]);
    const atom_site = Table.ofPartialColumns(BasicSchema.atom_site, {
        ...(authOnly ? {} : { label_comp_id: names }), auth_comp_id: names,
        Cartn_x: Column.ofFloatArray(xyz.subarray(0, 3)),
        Cartn_y: Column.ofFloatArray(xyz.subarray(3, 6)),
        Cartn_z: Column.ofFloatArray(xyz.subarray(6, 9)),
    }, 3);
    const chem_comp = category === "populated"
        ? Table.ofPartialColumns(BasicSchema.chem_comp, {
            id: names,
            type: Column.ofStringArray(["L-peptide linking", "D-saccharide", "non-polymer"]),
        }, 3)
        : Table.ofPartialColumns(BasicSchema.chem_comp, {}, 0);
    const data = createBasic({ atom_site, ...(category === "absent" ? {} : { chem_comp }) });
    const chemical = [...getChemicalComponentMap(data)];
    const saccharide = [...getSaccharideComponentMap(data)];
    assert.deepEqual(chemical.map(([key]) => key), ["ALA", "NAG", "HOH"]);
    assert.ok(saccharide.some(([key]) => key === "NAG"));
    return {
        summary: { index, category, authOnly, chemical, saccharide },
        refs: { data: new WeakRef(data), table: new WeakRef(atom_site), buffer: new WeakRef(xyz.buffer) },
    };
}

const summaries = [];
for (const category of ["absent", "empty", "populated"]) {
    for (const authOnly of [false, true]) summaries.push(visit(0, category, authOnly).summary);
}
const refs = Array.from({ length: 5 }, (_, index) => visit(index).refs);
assert.equal(typeof global.gc, "function", "This lifetime guard requires --expose-gc.");
for (let i = 0; i < 8; i++) { await setImmediate(); global.gc(); }
const retained = refs.map(row => ({
    data: !!row.data.deref(), table: !!row.table.deref(), buffer: !!row.buffer.deref(),
}));
console.log(JSON.stringify({ summaries, retained }));
