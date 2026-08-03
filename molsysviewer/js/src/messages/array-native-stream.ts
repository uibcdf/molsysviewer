import {
    ARRAY_NATIVE_PROTOCOL_VERSION,
    decodeStructuralArraySet,
    isStructuralArrayKind,
    type ArrayNativeMolSysMetadata,
    type DecodedArrayNativeMolSys,
    type StructureDataBeginMessage,
    type StructureDataCancelMessage,
    type StructureDataChunkMessage,
    type StructuralArrayKind,
} from "./array-native-transport";

type ActiveStream = {
    begin: StructureDataBeginMessage;
    nextChunkId: number;
    nextStructureStart: number;
    coordinates: Float32Array;
    box?: Float32Array;
    time?: Float64Array;
    kinds: Set<StructuralArrayKind>;
};

type StreamMessage =
    | StructureDataBeginMessage
    | StructureDataChunkMessage
    | StructureDataCancelMessage;

export function bindStreamEventToEndpoint(
    event: Record<string, unknown>,
    endpointId: string,
): Record<string, unknown> {
    return { ...event, target_endpoint_id: endpointId };
}

function positiveInteger(value: unknown, name: string): number {
    if (!Number.isInteger(value) || Number(value) <= 0) {
        throw new Error(`${name} must be a positive integer`);
    }
    return Number(value);
}

function metadataKinds(metadata: ArrayNativeMolSysMetadata): Set<StructuralArrayKind> {
    const nAtoms = positiveInteger(metadata.n_atoms, "n_atoms");
    const nStructures = positiveInteger(metadata.n_structures, "n_structures");
    if (
        metadata.protocol_version !== ARRAY_NATIVE_PROTOCOL_VERSION ||
        !metadata.atoms ||
        metadata.atoms.atom_id?.length !== nAtoms
    ) {
        throw new Error("Invalid array-native stream metadata");
    }
    const kinds = new Set<StructuralArrayKind>();
    const bufferIndices = new Set<number>();
    for (const descriptor of metadata.structural_arrays ?? []) {
        if (!isStructuralArrayKind(descriptor.kind)) {
            throw new Error(`Unsupported structural array kind ${String(descriptor.kind)}`);
        }
        if (kinds.has(descriptor.kind)) {
            throw new Error(`Duplicate structural array ${descriptor.kind}`);
        }
        kinds.add(descriptor.kind);
        if (
            !Number.isInteger(descriptor.buffer_index) ||
            descriptor.buffer_index < 0 ||
            bufferIndices.has(descriptor.buffer_index)
        ) {
            throw new Error(`Invalid complete buffer index for ${descriptor.kind}`);
        }
        bufferIndices.add(descriptor.buffer_index);
        const expectedShape =
            descriptor.kind === "coordinates" ? [nStructures, 3, nAtoms] :
            descriptor.kind === "box" ? [nStructures, 3, 3] :
            [nStructures];
        const bytesPerElement = descriptor.kind === "time" ? 8 : 4;
        const expectedDtype = descriptor.kind === "time" ? "float64" : "float32";
        const expectedUnits = descriptor.kind === "time" ? "ps" : "angstrom";
        const expectedLayout =
            descriptor.kind === "coordinates" ? "structure-planar-c" : "structure-major-c";
        const expectedBytes = expectedShape.reduce((total, item) => total * item, 1) * bytesPerElement;
        if (
            descriptor.dtype !== expectedDtype ||
            descriptor.units !== expectedUnits ||
            descriptor.layout !== expectedLayout ||
            descriptor.endianness !== "little" ||
            descriptor.shape.length !== expectedShape.length ||
            descriptor.shape.some((value, index) => value !== expectedShape[index]) ||
            descriptor.byte_length !== expectedBytes
        ) {
            throw new Error(`Invalid complete descriptor for ${descriptor.kind}`);
        }
    }
    if (!kinds.has("coordinates")) {
        throw new Error("Array-native stream requires coordinates");
    }
    if (
        bufferIndices.size !== kinds.size ||
        [...bufferIndices].some(index => index >= kinds.size)
    ) {
        throw new Error("Array-native stream descriptor indices are incomplete");
    }
    return kinds;
}

function identity(message: StreamMessage): string {
    return `${message.viewer_id}\u0000${message.session_id}\u0000${message.stream_id}`;
}

function targetIdentity(message: StreamMessage): Record<string, unknown> {
    return message.target_endpoint_id
        ? { target_endpoint_id: message.target_endpoint_id }
        : {};
}

export class ArrayNativeStreamReceiver {
    private endpointIdentity: string | null = null;
    private latestGeneration = 0;
    private active: ActiveStream | null = null;

    constructor(
        private readonly notify: (event: Record<string, unknown>) => void,
        private readonly onComplete: (
            begin: StructureDataBeginMessage,
            payload: DecodedArrayNativeMolSys,
        ) => Promise<void>,
    ) {}

    async handle(message: StreamMessage, buffers: readonly DataView[] = []): Promise<void> {
        try {
            if (message.op === "structure_data_begin") {
                this.begin(message);
                return;
            }
            if (message.op === "structure_data_cancel") {
                this.cancel(message);
                return;
            }
            await this.chunk(message, buffers);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.notify({
                event: "structure_data_error",
                viewer_id: message.viewer_id,
                session_id: message.session_id,
                stream_id: message.stream_id,
                generation: message.generation,
                ...targetIdentity(message),
                chunk_id: message.op === "structure_data_chunk" ? message.chunk_id : undefined,
                error: errorMessage,
            });
            if (
                message.op !== "structure_data_begin" &&
                this.active?.begin.generation === message.generation
            ) {
                this.active = null;
            }
            throw error;
        }
    }

    dispose(): void {
        this.active = null;
        this.endpointIdentity = null;
        this.latestGeneration = 0;
    }

    private begin(message: StructureDataBeginMessage): void {
        if (message.protocol_version !== ARRAY_NATIVE_PROTOCOL_VERSION) {
            throw new Error(`Unsupported array-native stream version ${message.protocol_version}`);
        }
        const incomingIdentity = identity(message);
        if (this.endpointIdentity !== null && incomingIdentity !== this.endpointIdentity) {
            throw new Error("Array-native stream identity does not belong to this endpoint");
        }
        if (!Number.isInteger(message.generation) || message.generation <= this.latestGeneration) {
            throw new Error(`Stale array-native generation ${message.generation}`);
        }
        const chunkCount = positiveInteger(message.chunk_count, "chunk_count");
        const kinds = metadataKinds(message.metadata);
        const nAtoms = message.metadata.n_atoms;
        const nStructures = message.metadata.n_structures;
        this.endpointIdentity = incomingIdentity;
        this.latestGeneration = message.generation;
        this.active = {
            begin: { ...message, chunk_count: chunkCount },
            nextChunkId: 0,
            nextStructureStart: 0,
            coordinates: new Float32Array(nStructures * nAtoms * 3),
            box: kinds.has("box") ? new Float32Array(nStructures * 9) : undefined,
            time: kinds.has("time") ? new Float64Array(nStructures) : undefined,
            kinds,
        };
        this.notify({
            event: "structure_data_begin_ack",
            viewer_id: message.viewer_id,
            session_id: message.session_id,
            stream_id: message.stream_id,
            generation: message.generation,
            ...targetIdentity(message),
        });
    }

    private cancel(message: StructureDataCancelMessage): void {
        if (
            this.active &&
            identity(message) === this.endpointIdentity &&
            message.generation === this.active.begin.generation
        ) {
            this.active = null;
        }
    }

    private async chunk(
        message: StructureDataChunkMessage,
        buffers: readonly DataView[],
    ): Promise<void> {
        const active = this.active;
        if (!active) {
            throw new Error("Late array-native chunk has no active generation");
        }
        if (message.protocol_version !== ARRAY_NATIVE_PROTOCOL_VERSION) {
            throw new Error(`Unsupported array-native stream version ${message.protocol_version}`);
        }
        if (
            identity(message) !== this.endpointIdentity ||
            message.generation !== active.begin.generation
        ) {
            throw new Error("Array-native chunk identity or generation mismatch");
        }
        if (
            message.chunk_id !== active.nextChunkId ||
            message.structure_start !== active.nextStructureStart
        ) {
            throw new Error("Duplicate, out-of-order, or non-contiguous array-native chunk");
        }
        const structureCount = positiveInteger(message.structure_count, "structure_count");
        const end = message.structure_start + structureCount;
        if (end > active.begin.metadata.n_structures) {
            throw new Error("Array-native chunk exceeds the declared structure range");
        }
        const chunkKinds = new Set(message.structural_arrays.map(item => item.kind));
        if (
            chunkKinds.size !== active.kinds.size ||
            [...active.kinds].some(kind => !chunkKinds.has(kind))
        ) {
            throw new Error("Array-native chunk arrays do not match the stream declaration");
        }

        const decoded = decodeStructuralArraySet(
            message.structural_arrays,
            buffers,
            active.begin.metadata.n_atoms,
            structureCount,
        );
        active.coordinates.set(
            decoded.coordinates,
            message.structure_start * active.begin.metadata.n_atoms * 3,
        );
        if (active.box && decoded.box) active.box.set(decoded.box, message.structure_start * 9);
        if (active.time && decoded.time) active.time.set(decoded.time, message.structure_start);
        active.nextChunkId += 1;
        active.nextStructureStart = end;
        this.notify({
            event: "structure_data_chunk_ack",
            viewer_id: message.viewer_id,
            session_id: message.session_id,
            stream_id: message.stream_id,
            generation: message.generation,
            chunk_id: message.chunk_id,
            ...targetIdentity(message),
        });

        if (active.nextChunkId !== active.begin.chunk_count) return;
        if (active.nextStructureStart !== active.begin.metadata.n_structures) {
            throw new Error("Array-native stream ended before all structures arrived");
        }

        this.active = null;
        await this.onComplete(active.begin, {
            atoms: active.begin.metadata.atoms,
            bonds: active.begin.metadata.bonds,
            meta: active.begin.metadata.meta,
            nAtoms: active.begin.metadata.n_atoms,
            nStructures: active.begin.metadata.n_structures,
            coordinates: active.coordinates,
            box: active.box,
            time: active.time,
        });
        this.notify({
            event: "structure_data_complete",
            viewer_id: message.viewer_id,
            session_id: message.session_id,
            stream_id: message.stream_id,
            generation: message.generation,
            ...targetIdentity(message),
        });
    }
}
