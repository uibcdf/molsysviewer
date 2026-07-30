import assert from "node:assert/strict";
import test from "node:test";

import { ArrayNativeStreamReceiver } from "../../src/messages/array-native-stream";
import type {
    StructureDataBeginMessage,
    StructureDataChunkMessage,
} from "../../src/messages/array-native-transport";

const identity = {
    viewer_id: "view-a",
    session_id: "session-a",
    stream_id: "structures:main",
};

function begin(generation = 1): StructureDataBeginMessage {
    return {
        op: "structure_data_begin",
        protocol_version: 1,
        ...identity,
        generation,
        chunk_count: 2,
        metadata: {
            protocol_version: 1,
            n_atoms: 2,
            n_structures: 2,
            atoms: { atom_id: [1, 2] },
            structural_arrays: [{
                kind: "coordinates",
                dtype: "float32",
                shape: [2, 3, 2],
                layout: "structure-planar-c",
                units: "angstrom",
                endianness: "little",
                buffer_index: 0,
                byte_length: 12 * 4,
            }],
        },
    };
}

function chunk(
    chunkId: number,
    start: number,
    values: number[],
    generation = 1,
): [StructureDataChunkMessage, DataView[]] {
    const coordinates = new Float32Array(values);
    return [{
        op: "structure_data_chunk",
        protocol_version: 1,
        ...identity,
        generation,
        chunk_id: chunkId,
        structure_start: start,
        structure_count: 1,
        structural_arrays: [{
            kind: "coordinates",
            dtype: "float32",
            shape: [1, 3, 2],
            layout: "structure-planar-c",
            units: "angstrom",
            endianness: "little",
            buffer_index: 0,
            byte_length: coordinates.byteLength,
        }],
    }, [new DataView(coordinates.buffer)]];
}

test("array-native stream assembles contiguous chunks, acknowledges, and releases", async () => {
    const events: Record<string, unknown>[] = [];
    const completed: number[][] = [];
    const receiver = new ArrayNativeStreamReceiver(
        event => events.push(event),
        async (_message, payload) => completed.push([...payload.coordinates]),
    );
    const first = chunk(0, 0, [0, 1, 2, 3, 4, 5]);
    const second = chunk(1, 1, [6, 7, 8, 9, 10, 11]);

    await receiver.handle(begin());
    await receiver.handle(...first);
    await receiver.handle(...second);

    assert.deepEqual(
        events.map(event => event.event),
        [
            "structure_data_begin_ack",
            "structure_data_chunk_ack",
            "structure_data_chunk_ack",
            "structure_data_complete",
        ],
    );
    assert.deepEqual(completed, [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]]);
    await assert.rejects(
        receiver.handle(...second),
        /Late array-native chunk has no active generation/,
    );
});

test("array-native stream rejects duplicate or out-of-order chunks", async () => {
    const events: Record<string, unknown>[] = [];
    const receiver = new ArrayNativeStreamReceiver(
        event => events.push(event),
        async () => undefined,
    );
    const second = chunk(1, 1, [6, 7, 8, 9, 10, 11]);

    await receiver.handle(begin());
    await assert.rejects(
        receiver.handle(...second),
        /Duplicate, out-of-order, or non-contiguous/,
    );
    assert.equal(events.at(-1)?.event, "structure_data_error");
});

test("array-native stream rejects stale generations and cross-viewer replacement", async () => {
    const receiver = new ArrayNativeStreamReceiver(
        () => undefined,
        async () => undefined,
    );
    await receiver.handle(begin(2));

    await assert.rejects(receiver.handle(begin(2)), /Stale array-native generation/);
    await receiver.handle(...chunk(0, 0, [0, 1, 2, 3, 4, 5], 2));
    const foreign = begin(3);
    foreign.viewer_id = "view-b";
    await assert.rejects(
        receiver.handle(foreign),
        /identity does not belong to this endpoint/,
    );
});

test("array-native stream rejects structural array kinds outside the protocol", async () => {
    const receiver = new ArrayNativeStreamReceiver(
        () => undefined,
        async () => undefined,
    );
    const invalid = begin();
    invalid.metadata.structural_arrays[0].kind = "velocities" as "coordinates";

    await assert.rejects(
        receiver.handle(invalid),
        /Unsupported structural array kind velocities/,
    );
});

test("array-native cancellation releases partial arrays and rejects late chunks", async () => {
    const receiver = new ArrayNativeStreamReceiver(
        () => undefined,
        async () => undefined,
    );
    await receiver.handle(begin());
    await receiver.handle({
        op: "structure_data_cancel",
        ...identity,
        generation: 1,
        reason: "replaced",
    });

    await assert.rejects(
        receiver.handle(...chunk(0, 0, [0, 1, 2, 3, 4, 5])),
        /Late array-native chunk has no active generation/,
    );
});
