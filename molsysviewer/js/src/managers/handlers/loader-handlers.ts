import { PluginContext } from "molstar/lib/mol-plugin/context";
import {
    LoadMolSysPayloadMessage,
    LoadMolSysPayloadRefMessage,
    LoadPdbIdMessage,
    LoadStructureFromUrlMessage,
    LoadStructureMessage,
} from "../../messages/viewer-messages";
import {
    ArrayNativeMolSysPayload,
    LoadedStructure,
    MolSysPayload,
    loadStructureFromArrayNativeMolSys,
    loadStructureFromMolSysPayload,
    loadStructureFromString,
    loadStructureFromUrl,
} from "../../plugin/structure";
import { decodeStructuralArraySet } from "../../messages/array-native-transport";

export interface LoaderCallbacks {
    clearGlobalRepresentations: () => Promise<void>;
    captureCurrentStructure: () => void;
    setLoadedStructure: (ls: LoadedStructure | undefined) => void;
    getLoadedStructure: () => LoadedStructure | undefined;
    setExpectedFrameCount?: (n: number | undefined) => void;
}

export class LoaderHandlers {
    constructor(private plugin: PluginContext, private callbacks: LoaderCallbacks) {}

    async loadFromString(msg: LoadStructureMessage) {
        const text = msg.data ?? msg.pdb ?? msg.pdb_text ?? "";
        if (!text || typeof text !== "string") {
            console.warn("[MolSysViewer] load message without data/pdb/pdb_text");
            return;
        }
        const format = msg.format ?? "pdb";
        const label = msg.label ?? "Structure";
        await this.loadFromStringInternal(text, format, label);
    }

    async loadMolSysPayload(msg: LoadMolSysPayloadMessage) {
        if (!msg.payload) {
            console.warn("[MolSysViewer] load_molsys_payload without payload");
            return;
        }
        await this.loadFromMolSysPayloadInternal(msg.payload, msg.label);
    }

    async loadMolSysPayloadRef(msg: LoadMolSysPayloadRefMessage) {
        const url = msg.ref?.url;
        if (!url || typeof url !== "string") {
            console.warn("[MolSysViewer] load_molsys_payload_ref without ref.url");
            return;
        }
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Could not fetch MolSys payload ref: ${response.status} ${response.statusText}`);
        }
        const payload = await response.json() as MolSysPayload;
        await this.loadFromMolSysPayloadInternal(payload, msg.label);
    }

    /**
     * Qt standalone: the structural arrays arrive as one binary blob served by
     * the `molsysviewer-payload` scheme, with the metadata in the message. The
     * blob is the arrays concatenated in descriptor order, so it is sliced back
     * apart here and decoded with the same validation the AnyWidget stream uses.
     */
    async loadMolSysArrayPayloadRef(msg: any) {
        const url = msg?.ref?.url;
        if (!url || typeof url !== "string") {
            console.warn("[MolSysViewer] load_molsys_array_payload_ref without ref.url");
            return;
        }
        const metadata = msg.metadata;
        if (!metadata?.structural_arrays) {
            console.warn("[MolSysViewer] load_molsys_array_payload_ref without metadata");
            return;
        }
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(
                `Could not fetch MolSys array payload ref: ${response.status} ${response.statusText}`,
            );
        }
        const blob = await response.arrayBuffer();

        let offset = 0;
        const views: DataView[] = [];
        for (const descriptor of metadata.structural_arrays) {
            const length = Number(descriptor.byte_length);
            if (!Number.isFinite(length) || length < 0 || offset + length > blob.byteLength) {
                throw new Error(
                    `Array-native ref blob is inconsistent at ${descriptor.kind}: ` +
                    `needs ${length} bytes at offset ${offset} of ${blob.byteLength}`,
                );
            }
            views.push(new DataView(blob, offset, length));
            offset += length;
        }
        if (offset !== blob.byteLength) {
            throw new Error(
                `Array-native ref blob has ${blob.byteLength - offset} trailing bytes`,
            );
        }

        const decoded = decodeStructuralArraySet(
            metadata.structural_arrays,
            views,
            metadata.n_atoms,
            metadata.n_structures,
        );
        await this.loadArrayNativeMolSysPayload({
            atoms: metadata.atoms,
            bonds: metadata.bonds,
            meta: metadata.meta,
            nAtoms: metadata.n_atoms,
            nStructures: metadata.n_structures,
            ...decoded,
        }, msg.label);
    }

    async loadArrayNativeMolSysPayload(payload: ArrayNativeMolSysPayload, label?: string) {
        this.callbacks.setExpectedFrameCount?.(payload.nStructures);
        await this.callbacks.clearGlobalRepresentations();
        const previous = this.callbacks.getLoadedStructure()?.data ?? this.callbacks.getLoadedStructure()?.trajectory;
        const loaded = await loadStructureFromArrayNativeMolSys(this.plugin, payload, label, {
            previous,
        });
        this.callbacks.setLoadedStructure(loaded);
        this.callbacks.captureCurrentStructure();
    }

    async loadFromUrl(msg: LoadStructureFromUrlMessage) {
        if (!msg.url || typeof msg.url !== "string") {
            console.warn("[MolSysViewer] load_structure_from_url without url");
            return;
        }
        await this.loadFromUrlInternal(msg.url, msg.format, msg.label);
    }

    async loadPdbId(msg: LoadPdbIdMessage) {
        const pdbId = msg.pdb_id?.trim();
        if (!pdbId) {
            console.warn("[MolSysViewer] load_pdb_id without pdb_id");
            return;
        }
        await this.loadPdbIdInternal(pdbId);
    }

    private async loadFromStringInternal(data: string, format: string, label?: string) {
        this.callbacks.setExpectedFrameCount?.(1);
        await this.callbacks.clearGlobalRepresentations();
        const previous = this.callbacks.getLoadedStructure()?.data ?? this.callbacks.getLoadedStructure()?.trajectory;
        const ls = await loadStructureFromString(this.plugin, data, format, label, {
            previous,
        });
        this.callbacks.setLoadedStructure(ls);
        this.callbacks.captureCurrentStructure();
    }

    private async loadFromUrlInternal(url: string, format?: string, label?: string) {
        this.callbacks.setExpectedFrameCount?.(1);
        await this.callbacks.clearGlobalRepresentations();
        const previous = this.callbacks.getLoadedStructure()?.data ?? this.callbacks.getLoadedStructure()?.trajectory;
        const ls = await loadStructureFromUrl(this.plugin, url, format, label, {
            previous,
        });
        this.callbacks.setLoadedStructure(ls);
        this.callbacks.captureCurrentStructure();
    }

    private async loadFromMolSysPayloadInternal(payload: MolSysPayload, label?: string) {
        this.callbacks.setExpectedFrameCount?.(payload.structures?.length);
        await this.callbacks.clearGlobalRepresentations();
        const previous = this.callbacks.getLoadedStructure()?.data ?? this.callbacks.getLoadedStructure()?.trajectory;
        const ls = await loadStructureFromMolSysPayload(this.plugin, payload, label, {
            previous,
        });
        this.callbacks.setLoadedStructure(ls);
        this.callbacks.captureCurrentStructure();
    }

    private async loadPdbIdInternal(pdbId: string) {
        const normalized = pdbId.trim().toUpperCase();
        const url = `https://files.rcsb.org/download/${normalized}.pdb`;
        await this.loadFromUrlInternal(url, "pdb", `PDB ${normalized}`);
    }
}
