import { MolSysViewerController } from "../../src/managers/viewer-controller";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { StructureSelection } from "molstar/lib/mol-model/structure/query";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { Vec2 } from "molstar/lib/mol-math/linear-algebra";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra/3d/vec3";
import { Vec4 } from "molstar/lib/mol-math/linear-algebra/3d/vec4";
import { cameraProject } from "molstar/lib/mol-canvas3d/camera/util";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateSelection } from "molstar/lib/mol-state";
import {
    clearStructureTransparency,
    setStructureTransparency,
} from "molstar/lib/mol-plugin-state/helpers/structure-transparency";
import { setSubtreeVisibility } from "molstar/lib/mol-plugin/behavior/static/state";
import { MsvPerAtomColorThemeProvider } from "../../src/themes/per-atom-color";
import { ArrayNativeStreamReceiver } from "../../src/messages/array-native-stream";
import { PopupHostManager } from "../../src/managers/popup-host";

declare global {
    // eslint-disable-next-line no-var
    var Harness: {
        createController: typeof createController;
        profileExclusiveOwnership: typeof profileExclusiveOwnership;
        profileExclusiveOwnershipMask: typeof profileExclusiveOwnershipMask;
        profileRegionVisibilityControl: typeof profileRegionVisibilityControl;
        probeExclusiveOwnershipPicking: typeof probeExclusiveOwnershipPicking;
        probeGlobalRepresentationOwnershipMask: typeof probeGlobalRepresentationOwnershipMask;
        probePerAtomColorDecorator: typeof probePerAtomColorDecorator;
        probeRegionOrderOwnership: typeof probeRegionOrderOwnership;
        inspectScene: typeof inspectScene;
        probeAtomColors: typeof probeAtomColors;
        inspectTaggedRefs: typeof inspectTaggedRefs;
        loadArrayNativeFixture: typeof loadArrayNativeFixture;
        probePopupChannel: typeof probePopupChannel;
        probeStructureDataRelay: typeof probeStructureDataRelay;
        probeWidgetSeam: typeof probeWidgetSeam;
    } | undefined;
}

export async function probePopupChannel(): Promise<{
    type: string;
    viewerId: string;
    sessionId: string;
    mode: string;
}> {
    const popupModule = `
        export function bootPopup() {
            const channel = window.molsysviewer_popup_channel;
            const targetOrigin = window.location.origin && window.location.origin !== "null"
                ? window.location.origin : "*";
            let messageCounter = 0;
            const send = (action, payload) => window.opener.postMessage({
                channel,
                envelope: {
                    protocolVersion: 1,
                    viewerId: channel.viewerId,
                    sessionId: channel.sessionId,
                    endpointId: channel.popupEndpointId,
                    targetEndpointId: channel.hostEndpointId,
                    messageId: channel.popupEndpointId + ":" + (++messageCounter),
                    direction: "event",
                    action,
                    payload,
                },
            }, targetOrigin);
            window.addEventListener("message", event => {
                const message = event.data;
                if (
                    event.source !== window.opener ||
                    !message ||
                    message.channel?.token !== channel.token ||
                    message.channel?.viewerId !== channel.viewerId ||
                    message.channel?.sessionId !== channel.sessionId ||
                    message.envelope?.endpointId !== channel.authorityEndpointId
                ) return;
                send("molsysviewer-log-from-popout", message.envelope.payload);
            });
            send("molsysviewer-pop-ready", null);
        }
    `;
    const moduleUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(popupModule)}`;
    const manager = new PopupHostManager({
        moduleUrl,
        viewerId: "e2e-popup-view",
        sessionId: "e2e-popup-session",
    });

    return new Promise((resolve, reject) => {
        const timeout = window.setTimeout(() => {
            cleanup();
            reject(new Error("Timed out waiting for authenticated popup relay"));
        }, 5000);
        const cleanup = () => {
            window.clearTimeout(timeout);
            window.removeEventListener("message", onMessage);
            manager.close();
        };
        const onMessage = (event: MessageEvent) => {
            const message = manager.receive(event);
            if (!message) return;
            if (message.type === "molsysviewer-pop-ready") {
                manager.isReady = true;
                // Real declared actions, so the probe exercises the channel as production
                // uses it and the manifest guard applies to it too.
                manager.send("molsysviewer-sync-ui", { value: 7 });
                return;
            }
            if (message.type === "molsysviewer-log-from-popout") {
                const channel = message.channel;
                cleanup();
                resolve({
                    type: message.type,
                    viewerId: channel.viewerId,
                    sessionId: channel.sessionId,
                    mode: channel.mode,
                });
            }
        };
        window.addEventListener("message", onMessage);
        void manager.open().catch(error => {
            cleanup();
            reject(error);
        });
    });
}

export async function loadArrayNativeFixture(controller: MolSysViewerController) {
    // Planar per structure: all x, then all y, then all z. Same three atoms as
    // the interleaved fixture it replaces — structure 0 at (0,0,0) (1,0,0)
    // (0,1,0) and structure 1 translated by +5 in x.
    const coordinates = new Float32Array([
        0, 1, 0,   // structure 0, x
        0, 0, 1,   // structure 0, y
        0, 0, 0,   // structure 0, z
        5, 6, 5,   // structure 1, x
        0, 0, 1,   // structure 1, y
        0, 0, 0,   // structure 1, z
    ]);
    const time = new Float64Array([0, 2]);
    const metadata = {
        protocol_version: 1,
        n_atoms: 3,
        n_structures: 2,
        atoms: {
            atom_id: [1, 2, 3],
            atom_name: ["N", "CA", "C"],
            element_symbol: ["N", "C", "C"],
            residue_id: [1, 1, 1],
            residue_name: ["GLY", "GLY", "GLY"],
            chain_id: ["A", "A", "A"],
            entity_id: ["1", "1", "1"],
            group_type: ["amino acid", "amino acid", "amino acid"],
        },
        structural_arrays: [
            {
                kind: "coordinates" as const,
                dtype: "float32" as const,
                shape: [2, 3, 3],
                layout: "structure-planar-c" as const,
                units: "angstrom" as const,
                endianness: "little" as const,
                buffer_index: 0,
                byte_length: coordinates.byteLength,
            },
            {
                kind: "time" as const,
                dtype: "float64" as const,
                shape: [2],
                layout: "structure-major-c" as const,
                units: "ps" as const,
                endianness: "little" as const,
                buffer_index: 1,
                byte_length: time.byteLength,
            },
        ],
    };
    const begin = {
        op: "structure_data_begin" as const,
        protocol_version: 1,
        viewer_id: "e2e-view",
        session_id: "e2e-session",
        stream_id: "structures:main",
        generation: 1,
        chunk_count: 2,
        metadata,
        label: "array-native-e2e",
        multiple_structures: true,
    };
    const events: string[] = [];
    const receiver = new ArrayNativeStreamReceiver(
        event => events.push(String(event.event)),
        async (message, payload) => controller.loadArrayNativeMolSysPayload(payload, message.label),
    );
    await receiver.handle(begin);
    for (let chunkId = 0; chunkId < 2; chunkId++) {
        const coordinateChunk = coordinates.subarray(chunkId * 9, (chunkId + 1) * 9);
        const timeChunk = time.subarray(chunkId, chunkId + 1);
        await receiver.handle({
            op: "structure_data_chunk",
            protocol_version: 1,
            viewer_id: "e2e-view",
            session_id: "e2e-session",
            stream_id: "structures:main",
            generation: 1,
            chunk_id: chunkId,
            structure_start: chunkId,
            structure_count: 1,
            structural_arrays: [
                {
                    ...metadata.structural_arrays[0],
                    shape: [1, 3, 3],
                    byte_length: coordinateChunk.byteLength,
                },
                {
                    ...metadata.structural_arrays[1],
                    shape: [1],
                    byte_length: timeChunk.byteLength,
                },
            ],
        }, [
            new DataView(
                coordinateChunk.buffer,
                coordinateChunk.byteOffset,
                coordinateChunk.byteLength,
            ),
            new DataView(timeChunk.buffer, timeChunk.byteOffset, timeChunk.byteLength),
        ]);
    }

    const profiled = controller as ProfileController;
    const structure = profiled.getStructureData();
    const loaded = (profiled as any).loadedStructure;
    const trajectoryCell = loaded?.trajectory
        ? profiled.plugin.state.data.cells.get(loaded.trajectory)
        : undefined;
    return {
        atomCount: structure?.elementCount ?? 0,
        frameCount: trajectoryCell?.obj?.data?.frameCount ?? 0,
        firstAtomX: structure?.models?.[0]?.atomicConformation?.x?.[0] ?? null,
        events,
    };
}

/**
 * What Mol* is actually rendering, read from the plugin state tree.
 *
 * Phase 14 exists because every claim about `alpha`, `quality`, inheritance and
 * colour fall-through had until now only been asserted against the *message* we
 * emitted, never against the representation Mol* built from it. So this reads
 * `transform.params.type` off the real cells and nothing else.
 */
export type RenderedRepresentation = {
    name: string;
    typeParams: Record<string, unknown>;
    hidden: boolean;
};

export type SceneSnapshot = {
    wholeVisible: boolean;
    wholeReprs: RenderedRepresentation[];
    regions: Record<string, {
        state: string;
        hidden: boolean;
        atomCount: number;
        reprs: RenderedRepresentation[];
    }>;
};

export function inspectTaggedRefs(
    controller: MolSysViewerController,
    kind: string,
    tag: string,
): Array<{ ref: string; exists: boolean; hidden: boolean }> {
    const profiled = controller as ProfileController;
    const key = `${kind}\u0000${tag}`;
    const refs = ((profiled.state as any).tagIndex as Map<string, Set<string>> | undefined)?.get(key) ?? new Set();
    return Array.from(refs).map(ref => {
        const cell = profiled.plugin.state.data.cells.get(ref);
        return {
            ref,
            exists: cell !== undefined,
            hidden: cell?.state?.isHidden === true,
        };
    });
}

function readRepresentation(plugin: any, ref: string): RenderedRepresentation | null {
    const cell = plugin.state.data.cells.get(ref);
    if (!cell) return null;
    const type = (cell.transform?.params as any)?.type;
    if (typeof type?.name !== "string") return null;
    return {
        name: type.name,
        typeParams: { ...(type.params ?? {}) },
        // Mol* stores "not rendered" as `state.isHidden` on the cell.
        hidden: cell.state?.isHidden === true,
    };
}

export function inspectScene(controller: MolSysViewerController): SceneSnapshot {
    const profiled = controller as ProfileController;
    const plugin = profiled.plugin;
    const state = profiled.state as any;

    const wholeReprs: RenderedRepresentation[] = [];
    for (const ref of (state.globalReprs ?? []) as Iterable<string>) {
        const repr = readRepresentation(plugin, ref);
        if (repr) wholeReprs.push(repr);
    }

    const regions: SceneSnapshot["regions"] = {};
    (state.regionIndex as Map<string, any> | undefined)?.forEach((entry, tag) => {
        const reprs: RenderedRepresentation[] = [];
        for (const ref of (entry.representations ?? []) as string[]) {
            const repr = readRepresentation(plugin, ref);
            if (repr) reprs.push(repr);
        }
        regions[tag] = {
            state: entry.representationState,
            hidden: entry.hidden === true,
            atomCount: Array.isArray(entry.atomIndices) ? entry.atomIndices.length : 0,
            reprs,
        };
    });

    return {
        wholeVisible: state.requestedGlobalHidden !== true,
        wholeReprs,
        regions,
    };
}

/**
 * The colour Mol* would paint at each requested atom, evaluated through the real
 * per-atom decorator theme rather than read back from the message we sent.
 *
 * `0xaaaaaa` is the grey the old `reset_colors()` painted over the whole system;
 * Contract B says an uncoloured atom must fall through to the structural theme
 * instead, so the e2e asserts against that exact value.
 */
export function probeAtomColors(
    controller: MolSysViewerController,
    atomIndices: number[],
): { colors: number[]; baseThemeName: string | null; themeName: string | null } {
    const profiled = controller as ProfileController;
    const structure = profiled.getStructureData();
    if (!structure) throw new Error("probeAtomColors requires a loaded structure.");

    const refs = Array.from(((profiled.state as any).globalReprs ?? []) as Iterable<string>)
        .filter((ref): ref is string => typeof ref === "string");
    const cell = refs[0] ? profiled.plugin.state.data.cells.get(refs[0]) : undefined;
    const colorTheme = cell?.transform?.params?.colorTheme;
    const base = colorTheme?.params?.base ?? { name: "element-symbol", params: {} };

    const theme = MsvPerAtomColorThemeProvider.factory({ structure } as any, { base } as any);
    const colors = atomIndices.map(index => {
        const location = atomLocation(structure, index);
        if (!location) throw new Error(`probeAtomColors could not build a location for atom ${index}.`);
        return Number(theme.color(location, false));
    });

    return {
        colors,
        themeName: colorTheme?.name ?? null,
        baseThemeName: base?.name ?? null,
    };
}

type ProfileController = MolSysViewerController & {
    plugin: any;
    loadedStructure?: { structure?: any };
    state: {
        buildSelectionFromAtomIndices(structure: unknown, atomIndices: number[]): unknown;
    };
};

type RegionOrderOwnershipCase = {
    case: string;
    lowerTag: string;
    upperTag: string;
    lowerMaskedAtoms: number;
    upperMaskedAtoms: number;
    lowerRecords: TransparencyRecord[];
    upperRecords: TransparencyRecord[];
};

type ExclusiveOwnershipProfileOptions = {
    atoms: number;
    ownedAtoms: number;
    toggles: number;
    paused: boolean;
    representation?: string;
};

type ExclusiveOwnershipToggleProfile = {
    index: number;
    regionVisible: boolean;
    wholeAtoms: number;
    regionToggleMs: number;
    removeMs: number;
    buildSelectionMs: number;
    bundleMs: number;
    componentCommitMs: number;
    addRepresentationMs: number;
    totalMs: number;
};

type ExclusiveOwnershipMaskToggleProfile = {
    index: number;
    regionVisible: boolean;
    maskedAtoms: number;
    regionToggleMs: number;
    clearTransparencyMs: number;
    buildSelectionMs: number;
    lociMs: number;
    applyTransparencyMs: number;
    totalMs: number;
};

type ExclusiveOwnershipComponentProbe = {
    wholeComponentRefsBeforeRegion: string[];
    wholeComponentRefsAfterRegion: string[];
    targetWholeComponentRefs: string[];
    regionComponentRef: string | null;
    regionIncludedInGetComponents: boolean;
};

type TransparencyRecord = {
    componentRef: string;
    representationRef: string;
    layerCount: number;
    layerValues: number[];
    atomCount: number;
    atomSetMatchesExpected: boolean;
};

type ExclusiveOwnershipInvariantProbe = {
    targetWholeComponentRefs: string[];
    regionComponentRef: string | null;
    wholeTransparencyRecords: TransparencyRecord[];
    regionTransparencyRecords: TransparencyRecord[];
    wholeMaskedAtoms: number;
    regionMaskedAtoms: number;
    expectedMaskedAtoms: number;
    wholeOwnedAtomsTransparent: boolean;
    regionOwnedAtomsOpaque: boolean;
    wholeUnownedAtomsOpaque: boolean;
};

type GlobalRepresentationOwnershipMaskProbe = {
    globalRepresentationRefs: string[];
    wholeComponentRepresentationCount: number;
    wholeTransparencyRecords: TransparencyRecord[];
    regionTransparencyRecords: TransparencyRecord[];
    expectedMaskedAtoms: number;
    wholeOwnedAtomsTransparent: boolean;
    regionOwnedAtomsOpaque: boolean;
};

type PerAtomColorDecoratorProbe = {
    representationRef: string;
    themeName: string | null;
    baseThemeName: string | null;
    coloredAtomColor: number;
    uncoloredAtomColor: number;
    coloredAtomUsesLayer: boolean;
    uncoloredAtomFallsThrough: boolean;
};

type PickingProbeCaseName = "owned-region-visible" | "unowned-region-visible" | "owned-region-hidden";

type PickingProbeCase = {
    case: PickingProbeCaseName;
    atomIndex: number;
    regionVisible: boolean;
    picked: boolean;
    source: "whole" | "region" | "other" | "none";
    representationRef: string | null;
    componentRef: string | null;
    atomIndices: number[];
    pickPoint: [number, number];
    invariantProbe: ExclusiveOwnershipInvariantProbe;
};

function atomRange(start: number, stop: number): number[] {
    return Array.from({ length: Math.max(0, stop - start) }, (_value, index) => start + index);
}

async function removeStateObject(plugin: any, ref: unknown): Promise<number> {
    if (ref === undefined || ref === null) return 0;
    const resolved = String(ref);
    const cells = plugin && plugin.state && plugin.state.data ? plugin.state.data.cells : undefined;
    if (cells && typeof cells.has === "function" && !cells.has(resolved)) return 0;
    const started = performance.now();
    await PluginCommands.State.RemoveObject(plugin, {
        state: plugin.state.data,
        ref: resolved,
        removeParentGhosts: true,
    });
    return performance.now() - started;
}

async function buildExclusiveWhole(
    controller: ProfileController,
    atomIndices: number[],
    representation: string,
): Promise<{ componentRef: unknown; profile: Omit<ExclusiveOwnershipToggleProfile, "index" | "regionVisible" | "wholeAtoms" | "regionToggleMs" | "removeMs" | "totalMs"> }> {
    const structure = controller.getStructureData();
    const structureRef = controller.loadedStructure ? controller.loadedStructure.structure : undefined;
    if (!structure || !structureRef) {
        throw new Error("Exclusive ownership profile requires a loaded structure.");
    }

    const selectionStarted = performance.now();
    const selection = controller.state.buildSelectionFromAtomIndices(structure, atomIndices);
    const buildSelectionMs = performance.now() - selectionStarted;
    if (!selection) throw new Error("Exclusive ownership profile produced an empty whole selection.");

    const bundleStarted = performance.now();
    const bundle = StructureElement.Bundle.fromSelection(selection as any);
    const bundleMs = performance.now() - bundleStarted;

    const commitStarted = performance.now();
    const component = controller.plugin.state.data
        .build()
        .to(structureRef)
        .apply(StateTransforms.Model.StructureComponent, {
            type: { name: "bundle", params: bundle },
            nullIfEmpty: true,
            label: "__exclusive_whole_profile__",
    });
    await component.commit({ revertOnError: false });
    const componentCommitMs = performance.now() - commitStarted;
    const componentRef = component.selector ? component.selector.ref : undefined;
    if (!component.selector || !component.selector.isOk || !componentRef) {
        throw new Error("Exclusive ownership profile failed to build whole component.");
    }

    const reprStarted = performance.now();
    await controller.plugin.builders.structure.representation.addRepresentation(
        componentRef,
        { type: representation },
        { tag: "__exclusive_whole_profile__" },
    );
    const addRepresentationMs = performance.now() - reprStarted;

    return {
        componentRef,
        profile: {
            buildSelectionMs,
            bundleMs,
            componentCommitMs,
            addRepresentationMs,
        },
    };
}

function getWholeComponents(controller: ProfileController): any[] {
    const structures = controller.plugin.managers.structure.hierarchy.current.structures;
    const last = structures.length ? structures[structures.length - 1] : undefined;
    return last && Array.isArray(last.components) ? last.components : [];
}

function componentRefs(components: any[]): string[] {
    return components
        .map((component) => {
            const ref = component && component.cell && component.cell.transform
                ? component.cell.transform.ref
                : component && component.transform
                    ? component.transform.ref
                    : component && component.ref
                        ? component.ref
                        : undefined;
            return typeof ref === "string" ? ref : "";
        })
        .filter((ref) => ref.length > 0);
}

function findComponentByRef(controller: ProfileController, componentRef: unknown): any | null {
    const ref = typeof componentRef === "string" ? componentRef : null;
    if (!ref) return null;
    const structures = controller.plugin.managers.structure.hierarchy.current.structures;
    for (const structureRef of structures) {
        for (const component of structureRef.components ?? []) {
            const [candidate] = componentRefs([component]);
            if (candidate === ref) return component;
        }
    }
    return null;
}

function getRegionComponentRef(controller: ProfileController, tag: string): string | null {
    const regionIndex = (controller.state as any).regionIndex;
    const entry = regionIndex && typeof regionIndex.get === "function" ? regionIndex.get(tag) : undefined;
    const component = entry ? entry.component : undefined;
    const ref = typeof component === "string"
        ? component
        : component && typeof component.ref === "string"
            ? component.ref
            : null;
    return ref;
}

function atomIndicesToLoci(structure: Structure, atomIndices: number[]): StructureElement.Loci | null {
    const target = new Set(atomIndices);
    const lociElements: { unit: Unit.Atomic; indices: any }[] = [];
    for (const unit of structure.units) {
        if (!Unit.isAtomic(unit)) continue;
        const matched: number[] = [];
        const elements = unit.elements;
        const count = OrderedSet.size(elements);
        for (let ordinal = 0; ordinal < count; ordinal++) {
            if (target.has(OrderedSet.getAt(elements, ordinal))) matched.push(ordinal);
        }
        if (matched.length > 0) lociElements.push({ unit, indices: SortedArray.ofSortedArray(matched) });
    }
    return lociElements.length > 0 ? StructureElement.Loci(structure, lociElements as any) : null;
}

function atomPosition(structure: Structure, atomIndex: number): Vec3 | null {
    const position = Vec3();
    for (const unit of structure.units) {
        if (!Unit.isAtomic(unit)) continue;
        const elements = unit.elements;
        const count = OrderedSet.size(elements);
        for (let ordinal = 0; ordinal < count; ordinal++) {
            const elementIndex = OrderedSet.getAt(elements, ordinal);
            if (elementIndex !== atomIndex) continue;
            unit.conformation.position(elementIndex, position);
            return position;
        }
    }
    return null;
}

function atomLocation(structure: Structure, atomIndex: number): StructureElement.Location | null {
    for (const unit of structure.units) {
        if (!Unit.isAtomic(unit)) continue;
        const elements = unit.elements;
        const count = OrderedSet.size(elements);
        for (let ordinal = 0; ordinal < count; ordinal++) {
            const elementIndex = OrderedSet.getAt(elements, ordinal);
            if (elementIndex === atomIndex) return StructureElement.Location.create(structure, unit, elementIndex);
        }
    }
    return null;
}

function lociAtomIndices(loci: any): number[] {
    if (!StructureElement.Loci.is(loci)) return [];
    const seen = new Set<number>();
    const atomIndices: number[] = [];
    for (const element of loci.elements) {
        const { unit, indices } = element;
        const count = OrderedSet.size(indices);
        for (let ordinal = 0; ordinal < count; ordinal++) {
            const unitIndex = OrderedSet.getAt(indices, ordinal);
            const atomIndex = OrderedSet.getAt(unit.elements, unitIndex);
            if (!seen.has(atomIndex)) {
                seen.add(atomIndex);
                atomIndices.push(atomIndex);
            }
        }
    }
    atomIndices.sort((left, right) => left - right);
    return atomIndices;
}

function bundleAtomIndices(bundle: StructureElement.Bundle, structure: Structure): number[] {
    const loci = StructureElement.Bundle.toLoci(bundle, structure);
    const atomIndices: number[] = [];
    for (const element of loci.elements) {
        const { unit, indices } = element;
        const size = OrderedSet.size(indices);
        for (let ordinal = 0; ordinal < size; ordinal++) {
            const unitIndex = OrderedSet.getAt(indices, ordinal);
            atomIndices.push(OrderedSet.getAt(unit.elements, unitIndex));
        }
    }
    atomIndices.sort((left, right) => left - right);
    return atomIndices;
}

function findPickedRepresentation(
    controller: ProfileController,
    repr: any,
    wholeComponentRefs: string[],
    regionComponentRef: string | null,
): { source: "whole" | "region" | "other" | "none"; representationRef: string | null; componentRef: string | null } {
    if (!repr) return { source: "none", representationRef: null, componentRef: null };
    const wholeRefs = new Set(wholeComponentRefs);
    const structures = controller.plugin.managers.structure.hierarchy.current.structures;
    for (const structureRef of structures) {
        for (const component of structureRef.components ?? []) {
            const [componentRef] = componentRefs([component]);
            for (const representation of component.representations ?? []) {
                const cell = representation.cell;
                if (cell && cell.obj && cell.obj.data && cell.obj.data.repr === repr) {
                    const representationRef = cell.transform.ref;
                    const source = componentRef === regionComponentRef
                        ? "region"
                        : wholeRefs.has(componentRef)
                            ? "whole"
                            : "other";
                    return { source, representationRef, componentRef };
                }
            }
        }
    }
    return { source: "other", representationRef: null, componentRef: null };
}

function identifyAtBestPoint(
    controller: ProfileController,
    atomIndex: number,
    wholeComponentRefs: string[],
    regionComponentRef: string | null,
): { picked: boolean; source: "whole" | "region" | "other" | "none"; representationRef: string | null; componentRef: string | null; atomIndices: number[]; pickPoint: [number, number] } {
    const structure = controller.getStructureData();
    const canvas3d = controller.plugin.canvas3d;
    if (!structure || !canvas3d) {
        return { picked: false, source: "none", representationRef: null, componentRef: null, atomIndices: [], pickPoint: [0, 0] };
    }
    const position = atomPosition(structure, atomIndex);
    if (!position) throw new Error(`Could not locate atom ${atomIndex}.`);
    const projected = cameraProject(Vec4(), position, canvas3d.camera.viewport, canvas3d.camera.projectionView);
    const viewport = canvas3d.camera.viewport;
    const candidates: Array<[number, number]> = [
        [projected[0], projected[1]],
        [projected[0], viewport.height - projected[1]],
        [viewport.width / 2, viewport.height / 2],
    ];
    for (const [x, y] of candidates) {
        const pick = canvas3d.identify(Vec2.create(x, y));
        const lociInfo = canvas3d.getLoci(pick ? pick.id : undefined);
        const picked = findPickedRepresentation(controller, lociInfo.repr, wholeComponentRefs, regionComponentRef);
        if (pick) {
            return {
                picked: true,
                ...picked,
                atomIndices: lociAtomIndices(lociInfo.loci),
                pickPoint: [x, y],
            };
        }
    }
    return { picked: false, source: "none", representationRef: null, componentRef: null, atomIndices: [], pickPoint: [projected[0], projected[1]] };
}

function sameAtomIndices(left: number[], right: number[]): boolean {
    if (left.length !== right.length) return false;
    for (let index = 0; index < left.length; index++) {
        if (left[index] !== right[index]) return false;
    }
    return true;
}

function transparencyRecords(plugin: any, components: any[], expectedAtomIndices: number[]): TransparencyRecord[] {
    const records: TransparencyRecord[] = [];
    const state = plugin.state.data;
    for (const component of components) {
        const [componentRef] = componentRefs([component]);
        const representations = Array.isArray(component.representations) ? component.representations : [];
        for (const representation of representations) {
            const cell = representation.cell;
            const representationRef = cell && cell.transform ? cell.transform.ref : undefined;
            const sourceData = cell && cell.obj && cell.obj.data ? cell.obj.data.sourceData : undefined;
            if (typeof representationRef !== "string" || !sourceData) continue;
            const transparencyCells = state.select(
                StateSelection.Generators.ofTransformer(
                    StateTransforms.Representation.TransparencyStructureRepresentation3DFromBundle,
                    representationRef,
                ).withTag("transparency-controls"),
            );
            for (const transparencyCell of transparencyCells) {
                const layers = transparencyCell.params && transparencyCell.params.values
                    ? transparencyCell.params.values.layers
                    : [];
                if (!Array.isArray(layers) || layers.length === 0) continue;
                let atomCount = 0;
                const layerValues: number[] = [];
                const transparentAtomIndices: number[] = [];
                for (const layer of layers) {
                    if (!layer || !layer.bundle) continue;
                    layerValues.push(Number(layer.value));
                    const atomIndices = bundleAtomIndices(layer.bundle, sourceData.root);
                    atomCount += atomIndices.length;
                    transparentAtomIndices.push(...atomIndices);
                }
                transparentAtomIndices.sort((left, right) => left - right);
                records.push({
                    componentRef,
                    representationRef,
                    layerCount: layers.length,
                    layerValues,
                    atomCount,
                    atomSetMatchesExpected: sameAtomIndices(transparentAtomIndices, expectedAtomIndices),
                });
            }
        }
    }
    return records;
}

function transparencyRecordsForRepresentationRefs(plugin: any, refs: string[], expectedAtomIndices: number[]): TransparencyRecord[] {
    const records: TransparencyRecord[] = [];
    const state = plugin.state.data;
    for (const representationRef of refs) {
        const cell = state.cells.get(representationRef);
        const sourceData = cell && cell.obj && cell.obj.data ? cell.obj.data.sourceData : undefined;
        if (!sourceData) continue;
        const transparencyCells = state.select(
            StateSelection.Generators.ofTransformer(
                StateTransforms.Representation.TransparencyStructureRepresentation3DFromBundle,
                representationRef,
            ).withTag("transparency-controls"),
        );
        for (const transparencyCell of transparencyCells) {
            const layers = transparencyCell.params && transparencyCell.params.values
                ? transparencyCell.params.values.layers
                : [];
            if (!Array.isArray(layers) || layers.length === 0) continue;
            let atomCount = 0;
            const layerValues: number[] = [];
            const transparentAtomIndices: number[] = [];
            for (const layer of layers) {
                if (!layer || !layer.bundle) continue;
                layerValues.push(Number(layer.value));
                const atomIndices = bundleAtomIndices(layer.bundle, sourceData.root);
                atomCount += atomIndices.length;
                transparentAtomIndices.push(...atomIndices);
            }
            transparentAtomIndices.sort((left, right) => left - right);
            records.push({
                componentRef: "__global_repr__",
                representationRef,
                layerCount: layers.length,
                layerValues,
                atomCount,
                atomSetMatchesExpected: sameAtomIndices(transparentAtomIndices, expectedAtomIndices),
            });
        }
    }
    return records;
}

function sumRecordAtoms(records: TransparencyRecord[]): number {
    return records.reduce((total, record) => total + record.atomCount, 0);
}

function recordsAreFullyTransparent(records: TransparencyRecord[]): boolean {
    return records.length > 0 && records.every((record) => (
        record.layerValues.length > 0 && record.layerValues.every((value) => value === 1)
    ));
}

function probeExclusiveOwnershipInvariant(
    controller: ProfileController,
    wholeComponents: any[],
    regionComponents: any[],
    regionComponentRef: string | null,
    expectedMaskedAtoms: number,
): ExclusiveOwnershipInvariantProbe {
    const expectedAtomIndices = atomRange(0, expectedMaskedAtoms);
    const wholeRecords = transparencyRecords(controller.plugin, wholeComponents, expectedAtomIndices);
    const regionRecords = transparencyRecords(controller.plugin, regionComponents, expectedAtomIndices);
    const wholeMaskedAtoms = sumRecordAtoms(wholeRecords);
    const regionMaskedAtoms = sumRecordAtoms(regionRecords);
    const targetWholeComponentRefs = componentRefs(wholeComponents);
    return {
        targetWholeComponentRefs,
        regionComponentRef,
        wholeTransparencyRecords: wholeRecords,
        regionTransparencyRecords: regionRecords,
        wholeMaskedAtoms,
        regionMaskedAtoms,
        expectedMaskedAtoms,
        wholeOwnedAtomsTransparent: wholeMaskedAtoms === expectedMaskedAtoms && recordsAreFullyTransparent(wholeRecords),
        regionOwnedAtomsOpaque: regionMaskedAtoms === 0 && regionRecords.length === 0,
        wholeUnownedAtomsOpaque: wholeRecords.length > 0 && wholeRecords.every((record) => record.atomSetMatchesExpected),
    };
}

function buildHiddenSelection(structure: Structure, hiddenAtomIndices: number[]): { selection: any; buildSelectionMs: number } {
    const started = performance.now();
    const selectionBuilder = StructureSelection.LinearBuilder(structure);
    const hiddenSet = new Set(hiddenAtomIndices);
    let hasHidden = false;

    for (const unit of structure.units) {
        if (!Unit.isAtomic(unit)) continue;
        const elementCount = OrderedSet.size(unit.elements);
        if (elementCount === 0) continue;

        const hiddenElements: number[] = [];
        for (let ordinal = 0; ordinal < elementCount; ordinal++) {
            const elementIndex = OrderedSet.getAt(unit.elements, ordinal);
            if (hiddenSet.has(elementIndex)) hiddenElements.push(elementIndex);
        }
        if (hiddenElements.length === 0) continue;
        hasHidden = true;

        const subset =
            hiddenElements.length === elementCount
                ? unit.elements
                : (SortedArray.ofSortedArray(hiddenElements) as StructureElement.Set);
        const childUnit = unit.getChild(subset);
        const hiddenStructure = Structure.create([childUnit], { parent: structure });
        selectionBuilder.add(hiddenStructure);
    }

    if (!hasHidden) return { selection: undefined, buildSelectionMs: performance.now() - started };
    return { selection: selectionBuilder.getSelection(), buildSelectionMs: performance.now() - started };
}

async function setRegionVisibility(controller: ProfileController, tag: string, visible: boolean): Promise<number> {
    const regionIndex = (controller.state as any).regionIndex;
    const entry = regionIndex && typeof regionIndex.get === "function" ? regionIndex.get(tag) : undefined;
    const refs = entry && Array.isArray(entry.representations) ? entry.representations : [];
    const started = performance.now();
    for (const ref of refs) {
        setSubtreeVisibility(controller.plugin.state.data, ref, !visible);
    }
    return performance.now() - started;
}

export async function createController(
    targetId = "root",
    options?: { isPanelOnly?: boolean; panelModeStyle?: string },
) {
    const target = document.getElementById(targetId) ?? document.body;
    (window as any).__messages = [];
    const controller = await MolSysViewerController.create(
        target,
        msg => {
            (window as any).__lastMessage = msg;
            (window as any).__messages.push(msg);
        },
        undefined,
        options,
    );
    (window as any).__controller = controller;
    return controller;
}

export async function profileExclusiveOwnership(
    controller: MolSysViewerController,
    options: ExclusiveOwnershipProfileOptions,
): Promise<ExclusiveOwnershipToggleProfile[]> {
    const profiled = controller as ProfileController;
    const atoms = Math.trunc(options.atoms);
    const ownedAtoms = Math.trunc(options.ownedAtoms);
    const toggles = Math.trunc(options.toggles);
    const representation = options.representation ?? "cartoon";
    if (atoms <= 0 || ownedAtoms <= 0 || ownedAtoms >= atoms || toggles <= 0) {
        throw new Error("Invalid exclusive ownership profile options.");
    }

    const canvas3d = profiled.plugin.canvas3d as { pause(value: boolean): void } | undefined;
    if (canvas3d) canvas3d.pause(options.paused);

    const owned = atomRange(0, ownedAtoms);
    const fullWhole = atomRange(0, atoms);
    const complementWhole = atomRange(ownedAtoms, atoms);

    await profiled.handleMessage({ op: "hide_whole", target: "whole" });
    await profiled.handleMessage({ op: "create_region", tag: "__exclusive_owned_region__", atom_indices: owned });
    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__exclusive_owned_region__",
        representation: "ball-and-stick",
    });

    let currentWhole = await buildExclusiveWhole(profiled, fullWhole, representation);
    const profiles: ExclusiveOwnershipToggleProfile[] = [];

    for (let index = 0; index < toggles; index++) {
        const regionVisible = index % 2 === 0;
        const wholeAtoms = regionVisible ? complementWhole : fullWhole;
        const totalStarted = performance.now();

        const regionToggleStarted = performance.now();
        await profiled.handleMessage({
            op: regionVisible ? "show_region" : "hide_region",
            tag: "__exclusive_owned_region__",
        });
        const regionToggleMs = performance.now() - regionToggleStarted;

        const removeMs = await removeStateObject(profiled.plugin, currentWhole.componentRef);
        currentWhole = await buildExclusiveWhole(profiled, wholeAtoms, representation);
        profiles.push({
            index,
            regionVisible,
            wholeAtoms: wholeAtoms.length,
            regionToggleMs,
            removeMs,
            ...currentWhole.profile,
            totalMs: performance.now() - totalStarted,
        });
    }

    await removeStateObject(profiled.plugin, currentWhole.componentRef);
    return profiles;
}

export async function profileExclusiveOwnershipMask(
    controller: MolSysViewerController,
    options: ExclusiveOwnershipProfileOptions,
): Promise<{ componentProbe: ExclusiveOwnershipComponentProbe; invariantProbe: ExclusiveOwnershipInvariantProbe | null; toggles: ExclusiveOwnershipMaskToggleProfile[] }> {
    const profiled = controller as ProfileController;
    const atoms = Math.trunc(options.atoms);
    const ownedAtoms = Math.trunc(options.ownedAtoms);
    const toggles = Math.trunc(options.toggles);
    if (atoms <= 0 || ownedAtoms <= 0 || ownedAtoms >= atoms || toggles <= 0) {
        throw new Error("Invalid exclusive ownership mask profile options.");
    }

    const structure = profiled.getStructureData();
    if (!structure) throw new Error("Exclusive ownership mask profile requires a loaded structure.");
    const canvas3d = profiled.plugin.canvas3d as { pause(value: boolean): void } | undefined;
    if (canvas3d) canvas3d.pause(options.paused);

    const wholeComponentsBeforeRegion = getWholeComponents(profiled);
    const refsBeforeRegion = componentRefs(wholeComponentsBeforeRegion);
    const owned = atomRange(0, ownedAtoms);

    await profiled.handleMessage({ op: "create_region", tag: "__exclusive_mask_region__", atom_indices: owned });
    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__exclusive_mask_region__",
        representation: "ball-and-stick",
    });

    const wholeComponentsAfterRegion = getWholeComponents(profiled);
    const refsAfterRegion = componentRefs(wholeComponentsAfterRegion);
    const regionComponentRef = getRegionComponentRef(profiled, "__exclusive_mask_region__");
    const componentProbe = {
        wholeComponentRefsBeforeRegion: refsBeforeRegion,
        wholeComponentRefsAfterRegion: refsAfterRegion,
        targetWholeComponentRefs: refsBeforeRegion,
        regionComponentRef,
        regionIncludedInGetComponents: regionComponentRef !== null && refsAfterRegion.includes(regionComponentRef),
    };

    const profiles: ExclusiveOwnershipMaskToggleProfile[] = [];
    const wholeComponents = wholeComponentsBeforeRegion;
    if (wholeComponents.length === 0) throw new Error("Exclusive ownership mask profile found no whole components.");
    const regionComponents = wholeComponentsAfterRegion.filter((component) => {
        const [ref] = componentRefs([component]);
        return regionComponentRef !== null && ref === regionComponentRef;
    });
    let invariantProbe: ExclusiveOwnershipInvariantProbe | null = null;

    for (let index = 0; index < toggles; index++) {
        const regionVisible = index % 2 === 0;
        const totalStarted = performance.now();

        const regionToggleMs = await setRegionVisibility(profiled, "__exclusive_mask_region__", regionVisible);

        const clearStarted = performance.now();
        await clearStructureTransparency(profiled.plugin, wholeComponents);
        const clearTransparencyMs = performance.now() - clearStarted;

        let buildSelectionMs = 0;
        let lociMs = 0;
        let applyTransparencyMs = 0;
        if (regionVisible) {
            const selectionResult = buildHiddenSelection(structure, owned);
            buildSelectionMs = selectionResult.buildSelectionMs;
            const selection = selectionResult.selection;
            if (!selection || StructureSelection.isEmpty(selection)) {
                throw new Error("Exclusive ownership mask profile produced an empty hidden selection.");
            }
            const lociStarted = performance.now();
            const loci = StructureSelection.toLociWithSourceUnits(selection);
            lociMs = performance.now() - lociStarted;

            const applyStarted = performance.now();
            await setStructureTransparency(profiled.plugin, wholeComponents, 1, async () => loci);
            applyTransparencyMs = performance.now() - applyStarted;

            const probe = probeExclusiveOwnershipInvariant(
                profiled,
                wholeComponents,
                regionComponents,
                regionComponentRef,
                ownedAtoms,
            );
            if (!probe.wholeOwnedAtomsTransparent || !probe.regionOwnedAtomsOpaque || !probe.wholeUnownedAtomsOpaque) {
                throw new Error(`Exclusive ownership mask invariant failed: ${JSON.stringify(probe)}`);
            }
            if (invariantProbe === null) invariantProbe = probe;
        }

        profiles.push({
            index,
            regionVisible,
            maskedAtoms: regionVisible ? owned.length : 0,
            regionToggleMs,
            clearTransparencyMs,
            buildSelectionMs,
            lociMs,
            applyTransparencyMs,
            totalMs: performance.now() - totalStarted,
        });
    }

    await clearStructureTransparency(profiled.plugin, wholeComponents);
    await setRegionVisibility(profiled, "__exclusive_mask_region__", false);
    return { componentProbe, invariantProbe, toggles: profiles };
}

export async function profileRegionVisibilityControl(
    controller: MolSysViewerController,
    options: ExclusiveOwnershipProfileOptions,
): Promise<ExclusiveOwnershipMaskToggleProfile[]> {
    const profiled = controller as ProfileController;
    const atoms = Math.trunc(options.atoms);
    const ownedAtoms = Math.trunc(options.ownedAtoms);
    const toggles = Math.trunc(options.toggles);
    if (atoms <= 0 || ownedAtoms <= 0 || ownedAtoms >= atoms || toggles <= 0) {
        throw new Error("Invalid region visibility control profile options.");
    }
    const canvas3d = profiled.plugin.canvas3d as { pause(value: boolean): void } | undefined;
    if (canvas3d) canvas3d.pause(options.paused);
    const owned = atomRange(0, ownedAtoms);
    await profiled.handleMessage({ op: "create_region", tag: "__visibility_control_region__", atom_indices: owned });
    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__visibility_control_region__",
        representation: "ball-and-stick",
    });
    const profiles: ExclusiveOwnershipMaskToggleProfile[] = [];
    for (let index = 0; index < toggles; index++) {
        const regionVisible = index % 2 === 0;
        const totalStarted = performance.now();
        const regionToggleMs = await setRegionVisibility(profiled, "__visibility_control_region__", regionVisible);
        profiles.push({
            index,
            regionVisible,
            maskedAtoms: 0,
            regionToggleMs,
            clearTransparencyMs: 0,
            buildSelectionMs: 0,
            lociMs: 0,
            applyTransparencyMs: 0,
            totalMs: performance.now() - totalStarted,
        });
    }
    await setRegionVisibility(profiled, "__visibility_control_region__", false);
    return profiles;
}

export async function probeExclusiveOwnershipPicking(
    controller: MolSysViewerController,
    options: { atoms: number; ownedAtoms: number; cases?: PickingProbeCaseName[]; cleanup?: boolean },
): Promise<{ cases: PickingProbeCase[]; pickabilityNotes: string[] }> {
    const profiled = controller as ProfileController;
    const atoms = Math.trunc(options.atoms);
    const ownedAtoms = Math.trunc(options.ownedAtoms);
    if (atoms <= 2 || ownedAtoms <= 0 || ownedAtoms >= atoms) {
        throw new Error("Invalid exclusive ownership picking probe options.");
    }
    const structure = profiled.getStructureData();
    if (!structure) throw new Error("Exclusive ownership picking probe requires a loaded structure.");

    const owned = atomRange(0, ownedAtoms);
    await profiled.handleMessage({ op: "hide_whole", target: "whole" });
    const explicitWhole = await buildExclusiveWhole(profiled, atomRange(0, atoms), "cartoon");
    const explicitWholeComponent = findComponentByRef(profiled, explicitWhole.componentRef);
    if (!explicitWholeComponent) throw new Error("Exclusive ownership picking probe failed to create explicit whole component.");
    const wholeComponentsBeforeRegion = [explicitWholeComponent];
    const refsBeforeRegion = componentRefs(wholeComponentsBeforeRegion);
    await profiled.handleMessage({ op: "create_region", tag: "__exclusive_pick_region__", atom_indices: owned });
    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__exclusive_pick_region__",
        representation: "ball-and-stick",
    });
    const regionComponentRef = getRegionComponentRef(profiled, "__exclusive_pick_region__");
    const wholeComponentsAfterRegion = getWholeComponents(profiled);
    const regionComponents = wholeComponentsAfterRegion.filter((component) => {
        const [ref] = componentRefs([component]);
        return regionComponentRef !== null && ref === regionComponentRef;
    });
    if (regionComponents.length === 0) throw new Error("Exclusive ownership picking probe could not find the region component.");
    const canvas3d = profiled.plugin.canvas3d;
    if (!canvas3d) throw new Error("Exclusive ownership picking probe requires Canvas3D.");

    async function runCase(name: PickingProbeCaseName, atomIndex: number, regionVisible: boolean): Promise<PickingProbeCase> {
        await setRegionVisibility(profiled, "__exclusive_pick_region__", regionVisible);
        await clearStructureTransparency(profiled.plugin, wholeComponentsBeforeRegion);
        const selectionResult = buildHiddenSelection(structure, owned);
        if (!selectionResult.selection || StructureSelection.isEmpty(selectionResult.selection)) {
            throw new Error("Exclusive ownership picking probe produced an empty hidden selection.");
        }
        const loci = StructureSelection.toLociWithSourceUnits(selectionResult.selection);
        await setStructureTransparency(profiled.plugin, wholeComponentsBeforeRegion, 1, async () => loci);
        const invariantProbe = probeExclusiveOwnershipInvariant(
            profiled,
            wholeComponentsBeforeRegion,
            regionComponents,
            regionComponentRef,
            ownedAtoms,
        );
        if (!invariantProbe.wholeOwnedAtomsTransparent || !invariantProbe.regionOwnedAtomsOpaque || !invariantProbe.wholeUnownedAtomsOpaque) {
            throw new Error(`Exclusive ownership picking invariant failed: ${JSON.stringify(invariantProbe)}`);
        }
        const focusLoci = atomIndicesToLoci(structure, [atomIndex]);
        if (!focusLoci) throw new Error(`Could not focus atom ${atomIndex}.`);
        profiled.plugin.managers.camera.focusLoci(focusLoci, { durationMs: 0, extraRadius: 1, minRadius: 1 });
        canvas3d.commit(true);
        canvas3d.requestDraw();
        await new Promise((resolve) => setTimeout(resolve, 120));
        const picked = identifyAtBestPoint(profiled, atomIndex, refsBeforeRegion, regionComponentRef);
        return {
            case: name,
            atomIndex,
            regionVisible,
            picked: picked.picked,
            source: picked.source,
            representationRef: picked.representationRef,
            componentRef: picked.componentRef,
            atomIndices: picked.atomIndices,
            pickPoint: picked.pickPoint,
            invariantProbe,
        };
    }

    const requestedCases = options.cases ?? [
        "owned-region-visible",
        "unowned-region-visible",
        "owned-region-hidden",
    ];
    const cases: PickingProbeCase[] = [];
    for (const caseName of requestedCases) {
        if (caseName === "owned-region-visible") {
            cases.push(await runCase("owned-region-visible", Math.min(1, ownedAtoms - 1), true));
        } else if (caseName === "unowned-region-visible") {
            cases.push(await runCase("unowned-region-visible", ownedAtoms, true));
        } else if (caseName === "owned-region-hidden") {
            cases.push(await runCase("owned-region-hidden", Math.min(1, ownedAtoms - 1), false));
        }
    }
    if (options.cleanup !== false) {
        await clearStructureTransparency(profiled.plugin, wholeComponentsBeforeRegion);
        await setRegionVisibility(profiled, "__exclusive_pick_region__", false);
        await removeStateObject(profiled.plugin, explicitWhole.componentRef);
    }
    return {
        cases,
        pickabilityNotes: [
            "Mol* exposes representation-level pickable state, not a per-loci pick mask equivalent to Transparency/Overpaint/Clipping.",
            "The pick shader discards fragments whose effective alpha is below the picking threshold, so full transparency can remove fragments from the pick pass.",
        ],
    };
}

export async function probeGlobalRepresentationOwnershipMask(
    controller: MolSysViewerController,
    options: { atoms: number; ownedAtoms: number; globalMessage: Record<string, unknown> },
): Promise<GlobalRepresentationOwnershipMaskProbe> {
    const profiled = controller as ProfileController;
    const atoms = Math.trunc(options.atoms);
    const ownedAtoms = Math.trunc(options.ownedAtoms);
    if (atoms <= 2 || ownedAtoms <= 0 || ownedAtoms >= atoms) {
        throw new Error("Invalid global representation ownership mask probe options.");
    }
    const owned = atomRange(0, ownedAtoms);
    await profiled.handleMessage({ op: "create_region", tag: "__global_mask_region__", atom_indices: owned });
    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__global_mask_region__",
        representation: "ball-and-stick",
    });
    await profiled.handleMessage({
        op: "set_whole_representation",
        ...options.globalMessage,
    } as any);

    const globalRepresentationRefs = Array.from(((profiled.state as any).globalReprs ?? []) as Iterable<string>)
        .filter((ref): ref is string => typeof ref === "string");
    const expectedAtomIndices = atomRange(0, ownedAtoms);
    const wholeTransparencyRecords = transparencyRecordsForRepresentationRefs(
        profiled.plugin,
        globalRepresentationRefs,
        expectedAtomIndices,
    );
    const regionComponentRef = getRegionComponentRef(profiled, "__global_mask_region__");
    const wholeComponents = getWholeComponents(profiled);
    const wholeComponentRepresentationCount = wholeComponents.reduce(
        (total, component) => total + (Array.isArray(component.representations) ? component.representations.length : 0),
        0,
    );
    const regionComponents = wholeComponents.filter((component) => {
        const [ref] = componentRefs([component]);
        return regionComponentRef !== null && ref === regionComponentRef;
    });
    const regionTransparencyRecords = transparencyRecords(profiled.plugin, regionComponents, expectedAtomIndices);
    return {
        globalRepresentationRefs,
        wholeComponentRepresentationCount,
        wholeTransparencyRecords,
        regionTransparencyRecords,
        expectedMaskedAtoms: ownedAtoms,
        wholeOwnedAtomsTransparent: sumRecordAtoms(wholeTransparencyRecords) === ownedAtoms
            && recordsAreFullyTransparent(wholeTransparencyRecords)
            && wholeTransparencyRecords.every((record) => record.atomSetMatchesExpected),
        regionOwnedAtomsOpaque: sumRecordAtoms(regionTransparencyRecords) === 0 && regionTransparencyRecords.length === 0,
    };
}

export async function probePerAtomColorDecorator(
    controller: MolSysViewerController,
    options: { coloredAtom: number; uncoloredAtom: number; color: number },
): Promise<PerAtomColorDecoratorProbe> {
    const profiled = controller as ProfileController;
    const structure = profiled.getStructureData();
    if (!structure) throw new Error("Per-atom color decorator probe requires a loaded structure.");

    await profiled.handleMessage({
        op: "set_whole_representation",
        representation: "ball-and-stick",
        params: { color_scheme: "element_cpk" },
    } as any);
    await profiled.handleMessage({
        op: "set_atom_colors",
        atom_indices: [options.coloredAtom],
        colors: [options.color],
        replace: true,
    });

    const globalRepresentationRefs = Array.from(((profiled.state as any).globalReprs ?? []) as Iterable<string>)
        .filter((ref): ref is string => typeof ref === "string");
    const representationRef = globalRepresentationRefs[0];
    if (!representationRef) throw new Error("Per-atom color decorator probe found no global representation ref.");
    const cell = profiled.plugin.state.data.cells.get(representationRef);
    const colorTheme = cell?.transform?.params?.colorTheme;
    const base = colorTheme?.params?.base;
    const coloredLocation = atomLocation(structure, options.coloredAtom);
    const uncoloredLocation = atomLocation(structure, options.uncoloredAtom);
    if (!coloredLocation || !uncoloredLocation) throw new Error("Per-atom color decorator probe could not build atom locations.");
    const theme = MsvPerAtomColorThemeProvider.factory(
        { structure } as any,
        { base: base ?? { name: "element-symbol", params: {} } } as any,
    );
    const coloredAtomColor = Number(theme.color(coloredLocation, false));
    const uncoloredAtomColor = Number(theme.color(uncoloredLocation, false));
    return {
        representationRef,
        themeName: colorTheme?.name ?? null,
        baseThemeName: base?.name ?? null,
        coloredAtomColor,
        uncoloredAtomColor,
        coloredAtomUsesLayer: coloredAtomColor === options.color,
        uncoloredAtomFallsThrough: uncoloredAtomColor !== 0xaaaaaa && uncoloredAtomColor !== options.color,
    };
}

export async function probeRegionOrderOwnership(
    controller: MolSysViewerController,
): Promise<{ cases: RegionOrderOwnershipCase[] }> {
    const profiled = controller as ProfileController;
    const structure = profiled.getStructureData();
    if (!structure) throw new Error("Region order ownership probe requires a loaded structure.");

    async function createRegion(tag: string, atomIndices: number[], order: number, alpha = 1) {
        await profiled.handleMessage({ op: "create_region", tag, atom_indices: atomIndices, order });
        await profiled.handleMessage({
            op: "set_region_representation",
            tag,
            order,
            representation: "ball-and-stick",
            params: { alpha },
        });
    }

    function regionComponents(tag: string) {
        const ref = getRegionComponentRef(profiled, tag);
        if (!ref) throw new Error(`Region order ownership probe could not find region component ${tag}.`);
        return getWholeComponents(profiled).filter((component) => {
            const [componentRef] = componentRefs([component]);
            return componentRef === ref;
        });
    }

    function recordCase(name: string, lowerTag: string, upperTag: string, expectedAtoms: number[]): RegionOrderOwnershipCase {
        const lowerRecords = transparencyRecords(profiled.plugin, regionComponents(lowerTag), expectedAtoms);
        const upperRecords = transparencyRecords(profiled.plugin, regionComponents(upperTag), expectedAtoms);
        return {
            case: name,
            lowerTag,
            upperTag,
            lowerMaskedAtoms: sumRecordAtoms(lowerRecords),
            upperMaskedAtoms: sumRecordAtoms(upperRecords),
            lowerRecords,
            upperRecords,
        };
    }

    await createRegion("__order_a__", [0, 1], 1);
    await createRegion("__order_b__", [1, 2], 2);
    const initial = recordCase("higher-order-region-masks-lower-overlap", "__order_a__", "__order_b__", [1]);

    await profiled.handleMessage({ op: "set_region_order", tag: "__order_a__", order: 3 });
    const raised = recordCase("raise-to-front-inverts-region-owner", "__order_b__", "__order_a__", [1]);

    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__order_b__",
        order: 4,
        representation: "ball-and-stick",
        params: { alpha: 0.95 },
    });
    const translucent = recordCase("translucent-higher-region-does-not-mask-lower", "__order_a__", "__order_b__", [1]);

    await profiled.handleMessage({
        op: "set_region_representation",
        tag: "__order_b__",
        order: 5,
        representation: "ball-and-stick",
        params: { alpha: 1 },
    });
    await profiled.handleMessage({
        op: "update_visibility",
        options: { visible_atom_indices: atomRange(1, 12), version: 1 },
    });
    const composed = recordCase("user-mask-and-region-ownership-coexist", "__order_a__", "__order_b__", [0, 1]);

    return { cases: [initial, raised, translucent, composed] };
}

if (typeof window !== "undefined") {
    (window as any).Harness = {
        createController,
        profileExclusiveOwnership,
        profileExclusiveOwnershipMask,
        profileRegionVisibilityControl,
        probeExclusiveOwnershipPicking,
        probeGlobalRepresentationOwnershipMask,
        probePerAtomColorDecorator,
        probeRegionOrderOwnership,
        inspectScene,
        probeAtomColors,
        inspectTaggedRefs,
        loadArrayNativeFixture,
        probePopupChannel,
        probeStructureDataRelay,
        probeWidgetSeam,
    };
}

/**
 * D4: the host relays an endpoint-addressed structure-data message to exactly
 * one popup, with its binary buffers intact across the real postMessage seam.
 *
 * The receiver itself is covered by the array-native E2E; what is unverified
 * here is the relay: that buffers survive structured clone byte for byte, that
 * only the addressed endpoint receives them, and that the popup's
 * acknowledgement travels back through the host.
 */
export async function probeStructureDataRelay(): Promise<{
    canvasReceived: number;
    panelReceived: number;
    bytesMatch: boolean;
    chunkId: number;
    ackAction: string;
}> {
    const popupModule = `
        export function bootPopup() {
            const channel = window.molsysviewer_popup_channel;
            const targetOrigin = window.location.origin && window.location.origin !== "null"
                ? window.location.origin : "*";
            let messageCounter = 0;
            const send = (action, payload) => window.opener.postMessage({
                channel,
                envelope: {
                    protocolVersion: 1,
                    viewerId: channel.viewerId,
                    sessionId: channel.sessionId,
                    endpointId: channel.popupEndpointId,
                    targetEndpointId: channel.hostEndpointId,
                    messageId: channel.popupEndpointId + ":" + (++messageCounter),
                    direction: "event",
                    action,
                    payload,
                },
            }, targetOrigin);
            window.addEventListener("message", event => {
                const message = event.data;
                if (
                    event.source !== window.opener ||
                    !message ||
                    message.channel?.token !== channel.token ||
                    message.envelope?.endpointId !== channel.authorityEndpointId
                ) return;
                if (message.envelope.action !== "molsysviewer-structure-data") return;
                // Report what actually crossed the seam: the chunk identity and
                // the bytes, so a corrupted or empty relay cannot pass.
                const payload = message.envelope.payload;
                const view = payload.buffers[0];
                const bytes = new Uint8Array(
                    view.buffer ?? view, view.byteOffset ?? 0, view.byteLength,
                );
                send("molsysviewer-structure-data-ack", {
                    event: "relay_probe",
                    mode: channel.mode,
                    chunk_id: payload.message.chunk_id,
                    bytes: Array.from(bytes),
                });
            });
            send("molsysviewer-pop-ready", null);
        }
    `;
    const moduleUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(popupModule)}`;
    const manager = new PopupHostManager({
        moduleUrl,
        viewerId: "e2e-relay-view",
        sessionId: "e2e-relay-session",
    });

    // A distinctive payload: if the relay drops or corrupts bytes, this fails.
    const source = new Uint8Array([1, 2, 3, 250, 251, 252]);

    return new Promise((resolve, reject) => {
        const counts = { canvas: 0, panel: 0 };
        const timeout = window.setTimeout(() => {
            cleanup();
            reject(new Error("Timed out waiting for the relayed structure-data ack"));
        }, 8000);
        const cleanup = () => {
            window.clearTimeout(timeout);
            window.removeEventListener("message", onMessage);
            manager.close("canvas");
            manager.close("panel");
        };
        const onMessage = (event: MessageEvent) => {
            const message = manager.receive(event);
            if (!message) return;
            if (message.type === "molsysviewer-pop-ready") {
                manager.isReady = true;
                const canvasEndpoint = manager.popupEndpointId("canvas");
                // Exactly what Python emits for a popup-addressed chunk.
                const relayed = {
                    op: "structure_data_chunk",
                    protocol_version: 1,
                    viewer_id: "e2e-relay-view",
                    session_id: "e2e-relay-session",
                    stream_id: "structures:main",
                    generation: 1,
                    chunk_id: 4,
                    structure_start: 0,
                    structure_count: 1,
                    target_endpoint_id: canvasEndpoint,
                    structural_arrays: [],
                };
                const view = new DataView(source.buffer, source.byteOffset, source.byteLength);
                counts.canvas += manager.sendTo("canvas", "molsysviewer-structure-data", {
                    message: relayed,
                    buffers: [view],
                }) ? 1 : 0;
                // No panel popup is open, so a panel-addressed relay must not land.
                counts.panel += manager.sendTo("panel", "molsysviewer-structure-data", {
                    message: relayed,
                    buffers: [view],
                }) ? 1 : 0;
                return;
            }
            if (message.type === "molsysviewer-structure-data-ack") {
                const data: any = message.data;
                cleanup();
                resolve({
                    canvasReceived: counts.canvas,
                    panelReceived: counts.panel,
                    bytesMatch: Array.isArray(data.bytes)
                        && data.bytes.length === source.length
                        && data.bytes.every((b: number, i: number) => b === source[i]),
                    chunkId: data.chunk_id,
                    ackAction: message.type,
                });
            }
        };
        window.addEventListener("message", onMessage);
        void manager.open("canvas").catch(error => {
            cleanup();
            reject(error);
        });
    });
}

/**
 * The AnyWidget seam, exercised in a real browser.
 *
 * R1's unit tests mirror the seam's decision logic; this drives the actual
 * `render({model, el})` entry point with a fake AnyWidget model and checks the
 * live `msg:custom` path: that `ready` leaves raw with its capabilities, that an
 * enveloped projection is unwrapped and applied, that a projection for another
 * session never lands, and that an outbound event is enveloped.
 */
export async function probeWidgetSeam(): Promise<{
    readyRaw: boolean;
    readyAdvertisesBinary: boolean;
    outboundEnveloped: boolean;
    projectionApplied: boolean;
    foreignSessionApplied: boolean;
}> {
    const viewerId = "e2e-seam-view";
    const sessionId = "e2e-seam-session";
    const traits: Record<string, unknown> = {
        runtime_viewer_id: viewerId,
        runtime_session_id: sessionId,
        initial_messages: [],
        enable_popout: false,
        debug_js: false,
        show_controls: false,
        autohide_controls: true,
        controls_mode: "classic",
        panel_mode_style: "drawer",
        viewer_mode: "integrated",
        controls_position: ["top", "right"],
        addon_states: {},
    };
    const sent: any[] = [];
    let customHandler: ((msg: any, buffers?: DataView[]) => void) | null = null;
    const model = {
        get: (key: string) => traits[key],
        set: () => {},
        save_changes: () => {},
        send: (msg: any) => sent.push(msg),
        on: (event: string, cb: any) => {
            if (event === "msg:custom") customHandler = cb;
        },
        off: () => {},
    };

    const el = document.createElement("div");
    Object.assign(el.style, { width: "640px", height: "480px" });
    document.body.appendChild(el);

    // Record what actually reaches the controller. Detecting the effect through
    // the DOM was tried first and made the test pass vacuously: nothing was
    // applied either way, so "a foreign session is not applied" held for the
    // wrong reason.
    const delivered: string[] = [];
    const controllerProto = MolSysViewerController.prototype as any;
    const originalHandle = controllerProto.handleMessage;
    controllerProto.handleMessage = function (msg: any, ...rest: any[]) {
        if (msg?.op) delivered.push(String(msg.op));
        return originalHandle.call(this, msg, ...rest);
    };

    const widget = (await import("../../src/index")).default;
    widget.render({ model, el });

    // `ready` is emitted once the runtime finished booting.
    const deadline = Date.now() + 20000;
    while (Date.now() < deadline && !sent.some(m => m?.event === "ready" || m?.payload?.event === "ready")) {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    const readyMessage = sent.find(m => m?.event === "ready" || m?.payload?.event === "ready");
    const readyRaw = !!readyMessage && readyMessage.event === "ready" && !("protocolVersion" in readyMessage);
    const readyAdvertisesBinary =
        Array.isArray(readyMessage?.capabilities?.binary_structure_data)
        && readyMessage.capabilities.binary_structure_data.includes(1);

    // An ordinary outbound event must leave enveloped.
    sent.length = 0;
    window.dispatchEvent(new Event("resize"));
    await new Promise(resolve => setTimeout(resolve, 400));
    const outboundEnveloped = sent.some(
        m => m?.protocolVersion === 1 && m?.direction === "event" && m?.payload?.event,
    );

    const projection = (overrides: Record<string, unknown> = {}) => ({
        protocolVersion: 1,
        viewerId,
        sessionId,
        endpointId: `python:${viewerId}`,
        targetEndpointId: `widget-host:${sessionId}`,
        messageId: "py-seam-1",
        direction: "projection",
        action: "set_legend",
        payload: { op: "set_legend", visible: true, title: "seam-probe" },
        ...overrides,
    });

    delivered.length = 0;
    customHandler?.(projection());
    await new Promise(resolve => setTimeout(resolve, 600));
    const projectionApplied = delivered.includes("set_legend");

    // Same projection, wrong session: must never reach the controller.
    delivered.length = 0;
    customHandler?.(projection({ sessionId: "someone-elses-session" }));
    await new Promise(resolve => setTimeout(resolve, 600));
    const foreignSessionApplied = delivered.includes("set_legend");

    controllerProto.handleMessage = originalHandle;

    return {
        readyRaw,
        readyAdvertisesBinary,
        outboundEnveloped,
        projectionApplied,
        foreignSessionApplied,
    };
}
