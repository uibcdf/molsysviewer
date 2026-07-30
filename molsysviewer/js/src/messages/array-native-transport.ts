import type { MolSysAtomPayload, MolSysPayload } from "../plugin/structure";

export const ARRAY_NATIVE_PROTOCOL_VERSION = 1;

export type StructuralArrayKind = "coordinates" | "box" | "time";

/**
 * `structure-planar-c` carries, per structure, all x then all y then all z, so
 * Mol*'s per-axis frames can be zero-copy subarray views. `structure-major-c`
 * is the interleaved xyz layout, still used by box and time.
 */
export type StructuralArrayLayout = "structure-major-c" | "structure-planar-c";

export type StructuralArrayDescriptor = {
    kind: StructuralArrayKind;
    dtype: "float32" | "float64";
    shape: number[];
    layout: StructuralArrayLayout;
    units: "angstrom" | "ps";
    endianness: "little";
    buffer_index: number;
    byte_length: number;
};

export type ArrayNativeMolSysMetadata = {
    protocol_version: number;
    n_atoms: number;
    n_structures: number;
    atoms: MolSysAtomPayload;
    bonds?: MolSysPayload["bonds"];
    meta?: Record<string, unknown>;
    structural_arrays: StructuralArrayDescriptor[];
};

export type LoadMolSysArrayPayloadMessage = {
    op: "load_molsys_array_payload";
    protocol_version: number;
    viewer_id: string;
    session_id: string;
    stream_id: string;
    generation: number;
    chunk_id: number;
    structure_start: number;
    structure_count: number;
    metadata: ArrayNativeMolSysMetadata;
    label?: string;
    multiple_structures?: boolean;
};

export type StructureDataBeginMessage = {
    op: "structure_data_begin";
    protocol_version: number;
    viewer_id: string;
    session_id: string;
    stream_id: string;
    generation: number;
    chunk_count: number;
    metadata: ArrayNativeMolSysMetadata;
    label?: string;
    multiple_structures?: boolean;
};

export type StructureDataChunkMessage = {
    op: "structure_data_chunk";
    protocol_version: number;
    viewer_id: string;
    session_id: string;
    stream_id: string;
    generation: number;
    chunk_id: number;
    structure_start: number;
    structure_count: number;
    structural_arrays: StructuralArrayDescriptor[];
};

export type StructureDataCancelMessage = {
    op: "structure_data_cancel";
    viewer_id: string;
    session_id: string;
    stream_id: string;
    generation: number;
    reason?: string;
};

export type DecodedArrayNativeMolSys = {
    atoms: MolSysAtomPayload;
    bonds?: MolSysPayload["bonds"];
    meta?: Record<string, unknown>;
    nAtoms: number;
    nStructures: number;
    coordinates: Float32Array;
    box?: Float32Array;
    time?: Float64Array;
};

export function isStructuralArrayKind(value: unknown): value is StructuralArrayKind {
    return value === "coordinates" || value === "box" || value === "time";
}

function requirePositiveInteger(value: unknown, name: string): number {
    if (!Number.isInteger(value) || Number(value) <= 0) {
        throw new Error(`${name} must be a positive integer`);
    }
    return Number(value);
}

function product(shape: readonly number[]): number {
    return shape.reduce((total, value) => total * value, 1);
}

function sameShape(actual: readonly number[], expected: readonly number[]): boolean {
    return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function typedView(
    buffer: DataView,
    descriptor: StructuralArrayDescriptor,
): Float32Array | Float64Array {
    const bytesPerElement = descriptor.dtype === "float32" ? 4 : 8;
    const expectedBytes = product(descriptor.shape) * bytesPerElement;
    if (descriptor.byte_length !== expectedBytes || buffer.byteLength !== expectedBytes) {
        throw new Error(
            `${descriptor.kind} byte length mismatch: descriptor=${descriptor.byte_length}, buffer=${buffer.byteLength}, expected=${expectedBytes}`,
        );
    }
    const length = expectedBytes / bytesPerElement;
    if (buffer.byteOffset % bytesPerElement === 0) {
        return descriptor.dtype === "float32"
            ? new Float32Array(buffer.buffer, buffer.byteOffset, length)
            : new Float64Array(buffer.buffer, buffer.byteOffset, length);
    }
    const copy = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
    return descriptor.dtype === "float32"
        ? new Float32Array(copy)
        : new Float64Array(copy);
}

export function decodeStructuralArraySet(
    descriptors: readonly StructuralArrayDescriptor[],
    buffers: readonly DataView[],
    nAtoms: number,
    nStructures: number,
): {
    coordinates: Float32Array;
    box?: Float32Array;
    time?: Float64Array;
} {
    if (!Array.isArray(descriptors as unknown)) {
        throw new Error("Array-native metadata requires structural array descriptors");
    }
    const decoded: Partial<Record<StructuralArrayKind, Float32Array | Float64Array>> = {};
    const usedBufferIndices = new Set<number>();
    for (const descriptor of descriptors) {
        if (!isStructuralArrayKind(descriptor.kind)) {
            throw new Error(`Unsupported structural array kind ${String(descriptor.kind)}`);
        }
        if (decoded[descriptor.kind]) {
            throw new Error(`Duplicate structural array ${descriptor.kind}`);
        }
        const expectedLayout =
            descriptor.kind === "coordinates" ? "structure-planar-c" : "structure-major-c";
        if (descriptor.layout !== expectedLayout || descriptor.endianness !== "little") {
            throw new Error(`Unsupported ${descriptor.kind} layout or endianness`);
        }
        if (!Number.isInteger(descriptor.buffer_index) || descriptor.buffer_index < 0) {
            throw new Error(`${descriptor.kind} has an invalid buffer index`);
        }
        if (usedBufferIndices.has(descriptor.buffer_index)) {
            throw new Error(`Structural arrays share buffer index ${descriptor.buffer_index}`);
        }
        usedBufferIndices.add(descriptor.buffer_index);
        const buffer = buffers[descriptor.buffer_index];
        if (!(buffer instanceof DataView)) {
            throw new Error(`${descriptor.kind} buffer ${descriptor.buffer_index} is missing`);
        }

        const expectedShape =
            descriptor.kind === "coordinates" ? [nStructures, 3, nAtoms] :
            descriptor.kind === "box" ? [nStructures, 3, 3] :
            [nStructures];
        const expectedDtype = descriptor.kind === "time" ? "float64" : "float32";
        const expectedUnits = descriptor.kind === "time" ? "ps" : "angstrom";
        if (
            descriptor.dtype !== expectedDtype ||
            descriptor.units !== expectedUnits ||
            !sameShape(descriptor.shape, expectedShape)
        ) {
            throw new Error(`Invalid ${descriptor.kind} dtype, units, or shape`);
        }
        decoded[descriptor.kind] = typedView(buffer, descriptor);
    }
    if (!(decoded.coordinates instanceof Float32Array)) {
        throw new Error("Array-native payload requires coordinates");
    }
    if (buffers.length !== descriptors.length || usedBufferIndices.size !== buffers.length) {
        throw new Error("Array-native payload contains unreferenced or missing buffers");
    }
    return {
        coordinates: decoded.coordinates,
        box: decoded.box as Float32Array | undefined,
        time: decoded.time as Float64Array | undefined,
    };
}

export function decodeArrayNativeMolSys(
    message: LoadMolSysArrayPayloadMessage,
    buffers: readonly DataView[],
): DecodedArrayNativeMolSys {
    if (message.protocol_version !== ARRAY_NATIVE_PROTOCOL_VERSION) {
        throw new Error(`Unsupported array-native protocol version ${message.protocol_version}`);
    }
    if (!message.viewer_id || !message.session_id || !message.stream_id) {
        throw new Error("Array-native envelope requires viewer, session, and stream identity");
    }
    if (!Number.isInteger(message.generation) || message.generation < 1) {
        throw new Error("Array-native envelope requires a positive generation");
    }
    if (message.chunk_id !== 0 || message.structure_start !== 0) {
        throw new Error("Array-native protocol D2a accepts one complete chunk only");
    }

    const metadata = message.metadata;
    if (!metadata || metadata.protocol_version !== ARRAY_NATIVE_PROTOCOL_VERSION) {
        throw new Error("Array-native metadata protocol does not match the envelope");
    }
    const nAtoms = requirePositiveInteger(metadata.n_atoms, "n_atoms");
    const nStructures = requirePositiveInteger(metadata.n_structures, "n_structures");
    if (message.structure_count !== nStructures) {
        throw new Error("Array-native structure_count does not match metadata");
    }
    if (!metadata.atoms || metadata.atoms.atom_id?.length !== nAtoms) {
        throw new Error("Array-native atom metadata does not match n_atoms");
    }
    const decoded = decodeStructuralArraySet(
        metadata.structural_arrays,
        buffers,
        nAtoms,
        nStructures,
    );

    return {
        atoms: metadata.atoms,
        bonds: metadata.bonds,
        meta: metadata.meta,
        nAtoms,
        nStructures,
        coordinates: decoded.coordinates,
        box: decoded.box as Float32Array | undefined,
        time: decoded.time as Float64Array | undefined,
    };
}
