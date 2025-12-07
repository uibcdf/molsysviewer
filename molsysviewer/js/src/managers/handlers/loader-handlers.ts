import { PluginContext } from "molstar/lib/mol-plugin/context";
import {
    LoadMolSysPayloadMessage,
    LoadPdbIdMessage,
    LoadStructureFromUrlMessage,
    LoadStructureMessage,
} from "../../messages/viewer-messages";
import {
    LoadedStructure,
    MolSysPayload,
    loadStructureFromMolSysPayload,
    loadStructureFromString,
    loadStructureFromUrl,
} from "../../plugin/structure";

export interface LoaderCallbacks {
    clearGlobalRepresentations: () => Promise<void>;
    captureCurrentStructure: () => void;
    setLoadedStructure: (ls: LoadedStructure | undefined) => void;
    getLoadedStructure: () => LoadedStructure | undefined;
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
        await this.callbacks.clearGlobalRepresentations();
        const previous = this.callbacks.getLoadedStructure()?.data ?? this.callbacks.getLoadedStructure()?.trajectory;
        const ls = await loadStructureFromString(this.plugin, data, format, label, {
            previous,
        });
        this.callbacks.setLoadedStructure(ls);
        this.callbacks.captureCurrentStructure();
    }

    private async loadFromUrlInternal(url: string, format?: string, label?: string) {
        await this.callbacks.clearGlobalRepresentations();
        const previous = this.callbacks.getLoadedStructure()?.data ?? this.callbacks.getLoadedStructure()?.trajectory;
        const ls = await loadStructureFromUrl(this.plugin, url, format, label, {
            previous,
        });
        this.callbacks.setLoadedStructure(ls);
        this.callbacks.captureCurrentStructure();
    }

    private async loadFromMolSysPayloadInternal(payload: MolSysPayload, label?: string) {
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
