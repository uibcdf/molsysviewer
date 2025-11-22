// src/shapes.ts

import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateObjectRef, StateTransformer } from "molstar/lib/mol-state";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";
import { Task, RuntimeContext } from "molstar/lib/mol-task";

import { Color } from "molstar/lib/mol-util/color";
import { ColorNames } from "molstar/lib/mol-util/color/names";

import { Vec3 } from "molstar/lib/mol-math/linear-algebra";

import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";

import { Structure, Unit, ElementIndex } from "molstar/lib/mol-model/structure";

import { Mesh } from "molstar/lib/mol-geo/geometry/mesh/mesh";
import { MeshBuilder } from "molstar/lib/mol-geo/geometry/mesh/mesh-builder";
import { addSphere } from "molstar/lib/mol-geo/geometry/mesh/builder/sphere";
import { addCylinder, BasicCylinderProps } from "molstar/lib/mol-geo/geometry/mesh/builder/cylinder";

import { Shape } from "molstar/lib/mol-model/shape";
import { ShapeRepresentation } from "molstar/lib/mol-repr/shape/representation";
import {
    Representation,
    RepresentationContext,
    RepresentationParamsGetter,
} from "molstar/lib/mol-repr/representation";

const MSVTransform = StateTransformer.builderFactory("molsysviewer");

export interface TransparentSphereSpec {
    center: [number, number, number];
    radius: number;
    color: number;
    alpha: number;
    id?: string;
}

interface TransparentSphereData {
    spheres: TransparentSphereSpec[];
}

const TransparentSphereParams = {
    ...Mesh.Params,
};
type TransparentSphereParams = typeof TransparentSphereParams;
type TransparentSphereProps = PD.Values<TransparentSphereParams>;

function buildSphereMesh(
    data: TransparentSphereData,
    _props: TransparentSphereProps,
    prev?: Mesh
): Mesh {
    const state = MeshBuilder.createState(128, 64, prev);
    const detail = 2;

    for (let i = 0, il = data.spheres.length; i < il; i++) {
        const s = data.spheres[i];
        state.currentGroup = i;
        addSphere(state, Vec3.create(s.center[0], s.center[1], s.center[2]), s.radius, detail);
    }

    return MeshBuilder.getMesh(state);
}

function getTransparentSphereName(data: TransparentSphereData) {
    if (data.spheres.length === 0) return "Transparent Sphere (empty)";
    if (data.spheres.length === 1) {
        const s = data.spheres[0];
        return s.id ? `Sphere ${s.id}` : "Transparent Sphere";
    }
    return `${data.spheres.length} Transparent Spheres`;
}

function getTransparentSphereShape(
    _ctx: RuntimeContext,
    data: TransparentSphereData,
    _props: TransparentSphereProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildSphereMesh(data, _props, shape?.geometry);
    const name = getTransparentSphereName(data);

    const getColor = (groupId: number) => Color(data.spheres[groupId].color);
    const getSize = (groupId: number) => data.spheres[groupId].radius;
    const getLabel = (groupId: number) => {
        const spec = data.spheres[groupId];
        const id = spec.id ?? `${groupId}`;
        return `Sphere ${id} (r = ${spec.radius.toFixed(2)})`;
    };

    return Shape.create(name, data, mesh, getColor, getSize, getLabel);
}

const TransparentSphereVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<TransparentSphereData, TransparentSphereParams>
    ) => ShapeRepresentation(getTransparentSphereShape, Mesh.Utils),
};

export const TransparentSphereShapeParams = {
    ...TransparentSphereParams,
};
export type TransparentSphereShapeParams = typeof TransparentSphereShapeParams;
export type TransparentSphereShapeProps = PD.Values<TransparentSphereShapeParams>;

export type TransparentSphereRepresentation = Representation<
    TransparentSphereData,
    TransparentSphereShapeParams
>;

export function TransparentSphereRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<TransparentSphereData, TransparentSphereShapeParams>
): TransparentSphereRepresentation {
    return Representation.createMulti(
        "TransparentSpheres",
        ctx,
        getParams,
        Representation.StateBuilder,
        TransparentSphereVisuals as unknown as Representation.Def<
            TransparentSphereData,
            TransparentSphereShapeParams
        >
    );
}

export const TransparentSphere3D = MSVTransform({
    name: "molsysviewer-transparent-sphere-3d",
    display: { name: "Transparent Sphere" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: {
        center: PD.Vec3(Vec3.create(0, 0, 0), { isEssential: true }),
        radius: PD.Numeric(1, { min: 0.01, max: 1000, step: 0.01 }, { isEssential: true }),
        color: PD.Color(ColorNames.green, { isEssential: true }),
        alpha: PD.Numeric(0.4, { min: 0, max: 1, step: 0.01 }, { isEssential: true }),
    },
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Transparent Sphere", async ctx => {
            const data: TransparentSphereData = {
                spheres: [
                    {
                        center: [params.center[0], params.center[1], params.center[2]],
                        radius: params.radius,
                        color: params.color,
                        alpha: params.alpha,
                        id: "sphere-0",
                    },
                ],
            };

            const repr = TransparentSphereRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => TransparentSphereShapeParams
            );

            const props: TransparentSphereShapeProps = {
                ...PD.getDefaultValues(TransparentSphereShapeParams),
            };

            await repr.createOrUpdate(props, data).runInContext(ctx);

            repr.setState({ alphaFactor: params.alpha });

            return new SO.Shape.Representation3D(
                { repr, sourceData: data },
                { label: "Transparent Sphere" }
            );
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Transparent Sphere", async ctx => {
            const data: TransparentSphereData = {
                spheres: [
                    {
                        center: [
                            newParams.center[0],
                            newParams.center[1],
                            newParams.center[2],
                        ],
                        radius: newParams.radius,
                        color: newParams.color,
                        alpha: newParams.alpha,
                        id: "sphere-0",
                    },
                ],
            };

            const props = { ...b.data.repr.props };
            await b.data.repr.createOrUpdate(props, data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.alpha });
            b.data.sourceData = data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

export async function addTransparentSphereFromPython(
    plugin: PluginContext,
    spec: TransparentSphereSpec
): Promise<StateObjectRef<SO.Shape.Representation3D>> {
    const centerVec = Vec3.create(spec.center[0], spec.center[1], spec.center[2]);

    const builder = plugin.state.data.build();
    const sphere = builder.toRoot().apply(
        TransparentSphere3D,
        {
            center: centerVec,
            radius: spec.radius,
            color: spec.color,
            alpha: spec.alpha,
        } as any,
        { tags: "molsysviewer:spheres" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return sphere.ref;
}

// ------------------------------------------------------------------
// Batch of transparent spheres in a single representation
// ------------------------------------------------------------------

const TransparentSpheresParams = {
    spheres: PD.Value<TransparentSphereSpec[]>([]),
    alpha: PD.Numeric(0.4, { min: 0, max: 1, step: 0.01 }, { isEssential: true }),
};
type TransparentSpheresParams = typeof TransparentSpheresParams;

export const TransparentSpheres3D = MSVTransform({
    name: "molsysviewer-transparent-spheres-3d",
    display: { name: "Transparent Spheres" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: TransparentSpheresParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Transparent Spheres", async ctx => {
            const data: TransparentSphereData = {
                spheres: params.spheres ?? [],
            };

            const repr = TransparentSphereRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => TransparentSphereShapeParams
            );

            const props: TransparentSphereShapeProps = {
                ...PD.getDefaultValues(TransparentSphereShapeParams),
            };

            await repr.createOrUpdate(props, data).runInContext(ctx);
            repr.setState({ alphaFactor: params.alpha });

            return new SO.Shape.Representation3D(
                { repr, sourceData: data },
                { label: "Transparent Spheres" }
            );
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Transparent Spheres", async ctx => {
            const data: TransparentSphereData = {
                spheres: newParams.spheres ?? [],
            };

            const props = { ...b.data.repr.props };
            await b.data.repr.createOrUpdate(props, data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.alpha });
            b.data.sourceData = data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

export async function addTransparentSpheresFromPython(
    plugin: PluginContext,
    spheres: TransparentSphereSpec[],
    alpha: number,
    tag?: string
): Promise<StateObjectRef<SO.Shape.Representation3D>> {
    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        TransparentSpheres3D,
        {
            spheres,
            alpha,
        } as any,
        { tags: tag ?? "molsysviewer:spheres" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}

// ------------------------------------------------------------------
// Network links (cylinders between point pairs)
// ------------------------------------------------------------------

type NetworkLinkColorMode = "link" | "pocket" | "chain";
type NetworkLinkMode = "coordinates" | "atom-indices";

const DefaultLinkPalette = [
    ColorNames.blue,
    ColorNames.orange,
    ColorNames.green,
    ColorNames.red,
    ColorNames.purple,
    ColorNames.gray,
    ColorNames.pink,
    ColorNames.brown,
];

export interface NetworkLinkSpec {
    start: [number, number, number];
    end: [number, number, number];
    radius: number;
    color: number;
    pocketId?: string | number;
    chainId?: string;
    label?: string;
}

interface NetworkLinksData {
    links: NetworkLinkSpec[];
    alpha: number;
    radialSegments: number;
    name: string;
    tag?: string;
}

const NetworkLinksParams = {
    ...Mesh.Params,
};
type NetworkLinksParams = typeof NetworkLinksParams;
type NetworkLinksProps = PD.Values<NetworkLinksParams>;

function buildNetworkLinkMesh(data: NetworkLinksData, _props: NetworkLinksProps, prev?: Mesh): Mesh {
    const state = MeshBuilder.createState(256, 128, prev);
    const start = Vec3();
    const end = Vec3();

    for (let i = 0, il = data.links.length; i < il; i++) {
        const link = data.links[i];
        state.currentGroup = i;
        Vec3.set(start, link.start[0], link.start[1], link.start[2]);
        Vec3.set(end, link.end[0], link.end[1], link.end[2]);

        const cylinderProps: BasicCylinderProps = {
            radiusTop: link.radius,
            radiusBottom: link.radius,
            radialSegments: Math.max(3, Math.floor(data.radialSegments)),
        };

        addCylinder(state, start, end, 1, cylinderProps);
    }

    return MeshBuilder.getMesh(state);
}

function getNetworkLinksName(count: number) {
    if (count === 0) return "Network Links (empty)";
    if (count === 1) return "Network Link";
    return `${count} Network Links`;
}

function getNetworkLinksShape(
    _ctx: RuntimeContext,
    data: NetworkLinksData,
    _props: NetworkLinksProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildNetworkLinkMesh(data, _props, shape?.geometry);
    const getColor = (groupId: number) => Color(data.links[groupId].color);
    const getSize = (groupId: number) => data.links[groupId].radius;
    const getLabel = (groupId: number) =>
        data.links[groupId].label ?? `Link ${groupId} (r = ${data.links[groupId].radius.toFixed(2)})`;

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const NetworkLinksVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<NetworkLinksData, NetworkLinksParams>
    ) => ShapeRepresentation(getNetworkLinksShape, Mesh.Utils),
};

type NetworkLinksRepresentation = Representation<NetworkLinksData, NetworkLinksParams>;

function NetworkLinksRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<NetworkLinksData, NetworkLinksParams>
): NetworkLinksRepresentation {
    return Representation.createMulti(
        "NetworkLinks",
        ctx,
        getParams,
        Representation.StateBuilder,
        NetworkLinksVisuals as unknown as Representation.Def<NetworkLinksData, NetworkLinksParams>
    );
}

const NetworkLinksTransformParams = {
    data: PD.Value<NetworkLinksData>(undefined as any),
    props: PD.Value<NetworkLinksProps>(undefined as any),
};

type NetworkLinksTransformParams = typeof NetworkLinksTransformParams;

export const NetworkLinks3D = MSVTransform({
    name: "molsysviewer-network-links-3d",
    display: { name: "Network Links" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: NetworkLinksTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Network Links", async ctx => {
            const repr = NetworkLinksRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => NetworkLinksParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: params.data.alpha });

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Network Links", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.data.alpha });
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

type CoordinatePair = [number, number, number, number, number, number] | [[number, number, number], [number, number, number]];

export interface NetworkLinkOptions {
    mode?: NetworkLinkMode;
    coordinate_pairs?: CoordinatePair[];
    atom_pairs?: [number, number][];
    radii?: number | number[];
    colors?: number | number[];
    pocket_ids?: Array<string | number>;
    chain_ids?: string[];
    color_mode?: NetworkLinkColorMode;
    alpha?: number;
    radial_segments?: number;
    tag?: string;
}

function normalizeCoordinatePair(entry: CoordinatePair): { start: [number, number, number]; end: [number, number, number] } | null {
    if (Array.isArray(entry[0])) {
        const start = (entry as [[number, number, number], [number, number, number]])[0];
        const end = (entry as [[number, number, number], [number, number, number]])[1];
        if (start.length === 3 && end.length === 3) {
            return {
                start: [Number(start[0]), Number(start[1]), Number(start[2])],
                end: [Number(end[0]), Number(end[1]), Number(end[2])],
            };
        }
        return null;
    }

    if (Array.isArray(entry) && entry.length === 6) {
        return {
            start: [Number(entry[0]), Number(entry[1]), Number(entry[2])],
            end: [Number(entry[3]), Number(entry[4]), Number(entry[5])],
        };
    }

    return null;
}

function expandToList<T>(value: T | T[] | undefined, count: number, cast: (v: T) => T, fallback: T): T[] {
    if (Array.isArray(value)) {
        if (value.length === count) return value.map(cast);
        console.warn(`[MolSysViewer] Esperaba ${count} valores pero recibí ${value.length}. Se reutilizará el primero.`);
        return Array(count).fill(cast(value[0]));
    }
    return Array(count).fill(cast((value ?? fallback) as T));
}

function prepareColorLookup(keys: Array<string | number>, fallback: number) {
    const paletteCount = DefaultLinkPalette.length;
    const colorByKey = new Map<string | number, number>();
    keys.forEach((key, idx) => {
        if (!colorByKey.has(key)) {
            colorByKey.set(key, DefaultLinkPalette[idx % paletteCount]);
        }
    });
    return (key?: string | number) => (key !== undefined ? colorByKey.get(key) ?? fallback : fallback);
}

function buildUnitLookup(structure: Structure) {
    const map = new Map<ElementIndex, { unit: Unit; elementIndex: ElementIndex }>();
    for (const unit of structure.units) {
        const { elements } = unit;
        const count = OrderedSet.size(elements);
        for (let i = 0; i < count; i++) {
            const element = OrderedSet.getAt(elements, i) as ElementIndex;
            map.set(element, { unit, elementIndex: element });
        }
    }
    return map;
}

function getChainId(unit: Unit, elementIndex: ElementIndex) {
    if (!Unit.isAtomic(unit)) return undefined;
    const chainIndex = unit.getChainIndex(elementIndex);
    return unit.model.atomicHierarchy.chains.label_asym_id.value(chainIndex);
}

function buildLinksFromCoordinates(options: NetworkLinkOptions): NetworkLinkSpec[] {
    const pairs = options.coordinate_pairs ?? [];
    const normalizedPairs = pairs
        .map(normalizeCoordinatePair)
        .filter((p): p is { start: [number, number, number]; end: [number, number, number] } => p !== null);

    const count = normalizedPairs.length;
    if (count === 0) return [];

    const radii = expandToList<number>(options.radii, count, Number, 0.2);
    const chainIds = expandToList<string>(options.chain_ids, count, String, "");
    const pocketIds = expandToList<string | number>(options.pocket_ids, count, v => v, "");
    const colorMode: NetworkLinkColorMode = options.color_mode ?? "link";
    const colors = expandToList<number>(options.colors, count, Number, ColorNames.skyblue);

    const paletteLookup = prepareColorLookup(colorMode === "pocket" ? pocketIds : chainIds, colors[0]);

    return normalizedPairs.map((pair, idx) => {
        const linkColor =
            colorMode === "link"
                ? colors[idx]
                : paletteLookup(colorMode === "pocket" ? pocketIds[idx] : chainIds[idx]);
        return {
            start: pair.start,
            end: pair.end,
            radius: radii[idx],
            color: linkColor,
            pocketId: pocketIds[idx],
            chainId: chainIds[idx] || undefined,
        };
    });
}

function buildLinksFromAtoms(structure: Structure, options: NetworkLinkOptions): NetworkLinkSpec[] {
    const pairs = options.atom_pairs ?? [];
    const count = pairs.length;
    if (count === 0) return [];

    const lookup = buildUnitLookup(structure);
    const radii = expandToList<number>(options.radii, count, Number, 0.2);
    const pocketIds = expandToList<string | number>(options.pocket_ids, count, v => v, "");
    const colorMode: NetworkLinkColorMode = options.color_mode ?? "link";
    const colors = expandToList<number>(options.colors, count, Number, ColorNames.skyblue);

    const positionsStart = Vec3();
    const positionsEnd = Vec3();

    const chainIdList: string[] = [];
    const specs: NetworkLinkSpec[] = [];

    for (let i = 0; i < count; i++) {
        const [a, b] = pairs[i];
        const locA = lookup.get(a as ElementIndex);
        const locB = lookup.get(b as ElementIndex);
        if (!locA || !locB) {
            console.warn(`[MolSysViewer] atom_pairs[${i}] no coincide con átomos de la estructura`);
            continue;
        }

        locA.unit.conformation.position(locA.elementIndex, positionsStart);
        locB.unit.conformation.position(locB.elementIndex, positionsEnd);

        const chainId = getChainId(locA.unit, locA.elementIndex) ?? getChainId(locB.unit, locB.elementIndex);
        chainIdList.push(chainId ?? "");

        specs.push({
            start: [positionsStart[0], positionsStart[1], positionsStart[2]],
            end: [positionsEnd[0], positionsEnd[1], positionsEnd[2]],
            radius: radii[i],
            color: colors[i],
            pocketId: pocketIds[i],
            chainId: chainId ?? undefined,
        });
    }

    if (specs.length === 0) return [];

    if (colorMode === "chain") {
        const paletteLookup = prepareColorLookup(chainIdList, colors[0]);
        specs.forEach((spec, idx) => {
            spec.color = paletteLookup(chainIdList[idx]);
        });
    } else if (colorMode === "pocket") {
        const paletteLookup = prepareColorLookup(pocketIds, colors[0]);
        specs.forEach(spec => {
            spec.color = paletteLookup(spec.pocketId);
        });
    }

    return specs;
}

export async function addNetworkLinksFromPython(plugin: PluginContext, options: NetworkLinkOptions) {
    const mode: NetworkLinkMode = options.mode ?? (options.atom_pairs ? "atom-indices" : "coordinates");
    const radialSegments = Math.max(3, Math.floor(options.radial_segments ?? 16));
    const alpha = options.alpha ?? 1.0;

    let links: NetworkLinkSpec[] = [];
    let name = "Network Links";

    if (mode === "atom-indices") {
        const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
        const structure = structureRef?.cell.obj?.data as Structure | undefined;
        if (!structure) {
            console.warn("[MolSysViewer] add_network_links sin estructura cargada");
            return undefined;
        }
        links = buildLinksFromAtoms(structure, options);
        name = getNetworkLinksName(links.length);
    } else {
        links = buildLinksFromCoordinates(options);
        name = getNetworkLinksName(links.length);
    }

    if (links.length === 0) {
        console.warn("[MolSysViewer] add_network_links sin datos válidos");
        return undefined;
    }

    const data: NetworkLinksData = {
        links,
        alpha,
        radialSegments,
        name,
        tag: options.tag,
    };

    const props: NetworkLinksProps = {
        ...PD.getDefaultValues(NetworkLinksParams),
    };

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        NetworkLinks3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:network-links" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}
