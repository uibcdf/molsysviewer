import assert from "node:assert/strict";
import test from "node:test";

import {
    decodeArrayNativeMolSys,
    type LoadMolSysArrayPayloadMessage,
} from "../../src/messages/array-native-transport";

function bufferView(values: Float32Array | Float64Array): DataView {
    return new DataView(values.buffer, values.byteOffset, values.byteLength);
}

function message(): LoadMolSysArrayPayloadMessage {
    return {
        op: "load_molsys_array_payload",
        protocol_version: 1,
        viewer_id: "view-a",
        session_id: "session-a",
        stream_id: "structures:main",
        generation: 1,
        chunk_id: 0,
        structure_start: 0,
        structure_count: 2,
        metadata: {
            protocol_version: 1,
            n_atoms: 2,
            n_structures: 2,
            atoms: {
                atom_id: [1, 2],
                atom_name: ["CA", "CB"],
            },
            structural_arrays: [
                {
                    kind: "coordinates",
                    dtype: "float32",
                    shape: [2, 3, 2],
                    layout: "structure-planar-c",
                    units: "angstrom",
                    endianness: "little",
                    buffer_index: 0,
                    byte_length: 12 * 4,
                },
                {
                    kind: "time",
                    dtype: "float64",
                    shape: [2],
                    layout: "structure-major-c",
                    units: "ps",
                    endianness: "little",
                    buffer_index: 1,
                    byte_length: 2 * 8,
                },
            ],
        },
    };
}

test("array-native decoder exposes typed structural arrays without nested coordinates", () => {
    const coordinates = new Float32Array([
        0, 1, 2, 3, 4, 5,
        6, 7, 8, 9, 10, 11,
    ]);
    const time = new Float64Array([0.5, 1.5]);

    const decoded = decodeArrayNativeMolSys(
        message(),
        [bufferView(coordinates), bufferView(time)],
    );

    assert.equal(decoded.nAtoms, 2);
    assert.equal(decoded.nStructures, 2);
    assert.deepEqual([...decoded.coordinates], [...coordinates]);
    assert.deepEqual([...(decoded.time ?? [])], [0.5, 1.5]);
    assert.equal(decoded.box, undefined);
});

test("array-native decoder rejects duplicate structural descriptors", () => {
    const msg = message();
    msg.metadata.structural_arrays[1] = {
        ...msg.metadata.structural_arrays[0],
        buffer_index: 1,
    };
    const coordinates = new Float32Array(12);

    assert.throws(
        () => decodeArrayNativeMolSys(
            msg,
            [bufferView(coordinates), bufferView(coordinates)],
        ),
        /Duplicate structural array coordinates/,
    );
});

test("array-native decoder rejects malformed byte lengths before constructing Molstar data", () => {
    const msg = message();
    const coordinates = new Float32Array(11);
    const time = new Float64Array(2);

    assert.throws(
        () => decodeArrayNativeMolSys(
            msg,
            [bufferView(coordinates), bufferView(time)],
        ),
        /coordinates byte length mismatch/,
    );
});

test("array-native decoder rejects descriptors that alias one transport buffer", () => {
    const msg = message();
    msg.metadata.structural_arrays[1].buffer_index = 0;
    const coordinates = new Float32Array(12);
    const time = new Float64Array(2);

    assert.throws(
        () => decodeArrayNativeMolSys(
            msg,
            [bufferView(coordinates), bufferView(time)],
        ),
        /share buffer index 0/,
    );
});

test("array-native decoder rejects incomplete D2a envelopes", () => {
    const msg = message();
    msg.structure_count = 1;
    const coordinates = new Float32Array(12);
    const time = new Float64Array(2);

    assert.throws(
        () => decodeArrayNativeMolSys(
            msg,
            [bufferView(coordinates), bufferView(time)],
        ),
        /structure_count does not match/,
    );
});
