// src/shapes.ts

import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateObjectRef, StateTransformer } from "molstar/lib/mol-state";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";
import { Task, RuntimeContext } from "molstar/lib/mol-task";

import { Color } from "molstar/lib/mol-util/color";
import { ColorNames } from "molstar/lib/mol-util/color/names";
import { ColorScale } from "molstar/lib/mol-util/color/scale";

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

// ------------------------------------------------------------------
// Triangle faces (custom meshes)
// ------------------------------------------------------------------

interface TriangleFaceSpec {
    vertices: [[number, number, number], [number, number, number], [number, number, number]];
    color: number;
    label?: string;
}

interface TriangleFacesData {
    triangles: TriangleFaceSpec[];
    alpha: number;
    name: string;
}

const TriangleFacesParams = {
    ...Mesh.Params,
};

type TriangleFacesParams = typeof TriangleFacesParams;
type TriangleFacesProps = PD.Values<TriangleFacesParams>;

function buildTriangleFacesMesh(data: TriangleFacesData, _props: TriangleFacesProps, prev?: Mesh): Mesh {
    const state = MeshBuilder.createState(256, 128, prev);
    const a = Vec3();
    const b = Vec3();
    const c = Vec3();

    for (let i = 0, il = data.triangles.length; i < il; i++) {
        const tri = data.triangles[i];
        state.currentGroup = i;
        Vec3.set(a, tri.vertices[0][0], tri.vertices[0][1], tri.vertices[0][2]);
        Vec3.set(b, tri.vertices[1][0], tri.vertices[1][1], tri.vertices[1][2]);
        Vec3.set(c, tri.vertices[2][0], tri.vertices[2][1], tri.vertices[2][2]);
        MeshBuilder.addTriangle(state, a, b, c);
    }

    return MeshBuilder.getMesh(state);
}

function getTriangleFacesShape(
    _ctx: RuntimeContext,
    data: TriangleFacesData,
    _props: TriangleFacesProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildTriangleFacesMesh(data, _props, shape?.geometry);
    const getColor = (groupId: number) => Color(data.triangles[groupId].color);
    const getSize = () => 1;
    const getLabel = (groupId: number) => data.triangles[groupId].label ?? `Triangle ${groupId}`;

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const TriangleFacesVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<TriangleFacesData, TriangleFacesParams>
    ) => ShapeRepresentation(getTriangleFacesShape, Mesh.Utils),
};

type TriangleFacesRepresentation = Representation<TriangleFacesData, TriangleFacesParams>;

function TriangleFacesRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<TriangleFacesData, TriangleFacesParams>
): TriangleFacesRepresentation {
    return Representation.createMulti(
        "TriangleFaces",
        ctx,
        getParams,
        Representation.StateBuilder,
        TriangleFacesVisuals as unknown as Representation.Def<TriangleFacesData, TriangleFacesParams>
    );
}

const TriangleFacesTransformParams = {
    data: PD.Value<TriangleFacesData>(undefined as any),
    props: PD.Value<TriangleFacesProps>(undefined as any),
};

type TriangleFacesTransformParams = typeof TriangleFacesTransformParams;

export const TriangleFaces3D = MSVTransform({
    name: "molsysviewer-triangle-faces-3d",
    display: { name: "Triangle Faces" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: TriangleFacesTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Triangle Faces", async ctx => {
            const repr = TriangleFacesRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => TriangleFacesParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: params.data.alpha });

            return new SO.Shape.Representation3D(
                { repr, sourceData: params.data },
                { label: params.data.name }
            );
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Triangle Faces", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.data.alpha });
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

type TriangleVerticesInput =
    | [number, number, number, number, number, number, number, number, number]
    | [[number, number, number], [number, number, number], [number, number, number]];

export interface TriangleFacesOptions {
    vertices?: TriangleVerticesInput[];
    atom_triplets?: number[][];
    atomTriplets?: number[][];
    colors?: number | number[];
    alpha?: number;
    labels?: string | string[];
    tag?: string;
}

function normalizeTriangle(entry: TriangleVerticesInput): TriangleFaceSpec["vertices"] | null {
    if (Array.isArray(entry) && entry.length === 3 && Array.isArray(entry[0])) {
        const verts = entry as [number[], number[], number[]];
        if (verts.every(v => Array.isArray(v) && v.length === 3)) {
            return verts.map(v => [Number(v[0]), Number(v[1]), Number(v[2])]) as TriangleFaceSpec["vertices"];
        }
    }

    if (Array.isArray(entry) && entry.length === 9) {
        return [
            [Number(entry[0]), Number(entry[1]), Number(entry[2])],
            [Number(entry[3]), Number(entry[4]), Number(entry[5])],
            [Number(entry[6]), Number(entry[7]), Number(entry[8])],
        ];
    }

    return null;
}

function expandOptionalToList<T>(value: T | T[] | undefined, count: number, cast: (v: T) => T): (T | undefined)[] {
    if (value === undefined) return Array(count).fill(undefined);
    if (Array.isArray(value)) {
        if (value.length === count) return value.map(cast);
        console.warn(`[MolSysViewer] Esperaba ${count} valores pero recibí ${value.length}. Se reutilizará el primero.`);
        return Array(count).fill(cast(value[0] as T));
    }
    return Array(count).fill(cast(value));
}

function buildTrianglesFromVertices(options: TriangleFacesOptions): TriangleFaceSpec[] {
    const input = options.vertices ?? [];
    const normalized = input
        .map(normalizeTriangle)
        .filter((v): v is TriangleFaceSpec["vertices"] => v !== null);

    const count = normalized.length;
    if (count === 0) return [];

    const colors = expandToList<number>(options.colors, count, Number, ColorNames.orange);
    const labels = expandOptionalToList<string>(options.labels, count, String);

    return normalized.map((verts, idx) => ({
        vertices: verts,
        color: colors[idx],
        label: labels[idx],
    }));
}

function buildTrianglesFromAtoms(structure: Structure, options: TriangleFacesOptions): TriangleFaceSpec[] {
    const triplets = options.atom_triplets ?? options.atomTriplets ?? [];
    if (triplets.length === 0) return [];

    const lookup = buildUnitLookup(structure);
    const a = Vec3();
    const b = Vec3();
    const c = Vec3();

    const colors = expandToList<number>(options.colors, triplets.length, Number, ColorNames.orange);
    const labels = expandOptionalToList<string>(options.labels, triplets.length, String);

    const triangles: TriangleFaceSpec[] = [];

    for (let i = 0; i < triplets.length; i++) {
        const triplet = triplets[i];
        if (!Array.isArray(triplet) || triplet.length !== 3) {
            console.warn(`[MolSysViewer] atom_triplets[${i}] no es un triplete válido`);
            continue;
        }

        const locA = lookup.get(triplet[0] as ElementIndex);
        const locB = lookup.get(triplet[1] as ElementIndex);
        const locC = lookup.get(triplet[2] as ElementIndex);
        if (!locA || !locB || !locC) {
            console.warn(`[MolSysViewer] atom_triplets[${i}] no coincide con átomos de la estructura`);
            continue;
        }

        locA.unit.conformation.position(locA.elementIndex, a);
        locB.unit.conformation.position(locB.elementIndex, b);
        locC.unit.conformation.position(locC.elementIndex, c);

        triangles.push({
            vertices: [
                [a[0], a[1], a[2]],
                [b[0], b[1], b[2]],
                [c[0], c[1], c[2]],
            ],
            color: colors[i],
            label: labels[i],
        });
    }

    return triangles;
}

function prepareTriangleFacesData(plugin: PluginContext, options: TriangleFacesOptions): TriangleFacesData | undefined {
    const alpha = options.alpha ?? 1.0;
    let triangles: TriangleFaceSpec[] = [];

    const atomTriplets = options.atom_triplets ?? options.atomTriplets;

    if (atomTriplets && atomTriplets.length > 0) {
        const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
        const structure = structureRef?.cell.obj?.data as Structure | undefined;
        if (!structure) {
            console.warn("[MolSysViewer] add_triangle_faces con atom_triplets pero sin estructura cargada");
            return undefined;
        }
        triangles = buildTrianglesFromAtoms(structure, options);
    } else {
        triangles = buildTrianglesFromVertices(options);
    }

    if (triangles.length === 0) {
        console.warn("[MolSysViewer] add_triangle_faces sin triángulos válidos");
        return undefined;
    }

    const name = triangles.length === 1 ? "Triangle Face" : `${triangles.length} Triangle Faces`;

    return {
        triangles,
        alpha,
        name,
    };
}

export async function addTriangleFacesFromPython(
    plugin: PluginContext,
    options: TriangleFacesOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | undefined> {
    const data = prepareTriangleFacesData(plugin, options);
    if (!data) return undefined;

    const props: TriangleFacesProps = {
        ...PD.getDefaultValues(TriangleFacesParams),
    };

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        TriangleFaces3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:triangle-faces" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}

// ------------------------------------------------------------------
// Displacement vectors (arrows)
// ------------------------------------------------------------------

interface DisplacementArrowSpec {
    start: [number, number, number];
    end: [number, number, number];
    length: number;
    value: number;
    color: number;
}

interface DisplacementVectorData {
    arrows: DisplacementArrowSpec[];
    radiusScale: number;
    radialSegments: number;
    name: string;
}

const DisplacementVectorParams = {
    ...Mesh.Params,
};

type DisplacementVectorParams = typeof DisplacementVectorParams;
type DisplacementVectorProps = PD.Values<DisplacementVectorParams>;

function buildDisplacementVectorMesh(
    data: DisplacementVectorData,
    _props: DisplacementVectorProps,
    prev?: Mesh
): Mesh {
    const state = MeshBuilder.createState(256, 128, prev);
    const start = Vec3();
    const end = Vec3();
    const dir = Vec3();
    const tipBase = Vec3();

    for (let i = 0, il = data.arrows.length; i < il; i++) {
        const arrow = data.arrows[i];
        state.currentGroup = i;

        Vec3.set(start, arrow.start[0], arrow.start[1], arrow.start[2]);
        Vec3.set(end, arrow.end[0], arrow.end[1], arrow.end[2]);
        Vec3.sub(dir, end, start);

        const length = arrow.length;
        if (length < 1e-4) continue;

        const radialSegments = Math.max(3, Math.floor(data.radialSegments));
        const shaftRadius = Math.max(0.01, length * data.radiusScale);
        const headRadius = shaftRadius * 1.8;
        const headLength = Math.max(length * 0.2, headRadius * 2.5);
        const shaftLength = Math.max(0, length - headLength);

        Vec3.scale(dir, dir, 1 / length);
        Vec3.scaleAndAdd(tipBase, start, dir, shaftLength);

        addCylinder(state, start, tipBase, 1, {
            radiusTop: shaftRadius,
            radiusBottom: shaftRadius,
            radialSegments,
        });

        addCylinder(state, tipBase, end, 1, {
            radiusTop: 0.0001,
            radiusBottom: headRadius,
            radialSegments,
        });
    }

    return MeshBuilder.getMesh(state);
}

function getDisplacementVectorShape(
    _ctx: RuntimeContext,
    data: DisplacementVectorData,
    _props: DisplacementVectorProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildDisplacementVectorMesh(data, _props, shape?.geometry);
    const getColor = (groupId: number) => Color(data.arrows[groupId].color);
    const getSize = (groupId: number) => data.arrows[groupId].length;
    const getLabel = (groupId: number) => {
        const arrow = data.arrows[groupId];
        return `Vector ${groupId}: |v|=${arrow.length.toFixed(2)}, value=${arrow.value.toFixed(2)}`;
    };

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const DisplacementVectorVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<DisplacementVectorData, DisplacementVectorParams>
    ) => ShapeRepresentation(getDisplacementVectorShape, Mesh.Utils),
};

type DisplacementVectorRepresentation = Representation<DisplacementVectorData, DisplacementVectorParams>;

function DisplacementVectorRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<DisplacementVectorData, DisplacementVectorParams>
): DisplacementVectorRepresentation {
    return Representation.createMulti(
        "DisplacementVectors",
        ctx,
        getParams,
        Representation.StateBuilder,
        DisplacementVectorVisuals as unknown as Representation.Def<
            DisplacementVectorData,
            DisplacementVectorParams
        >
    );
}

const DisplacementVectorTransformParams = {
    data: PD.Value<DisplacementVectorData>(undefined as any),
    props: PD.Value<DisplacementVectorProps>(undefined as any),
};

type DisplacementVectorTransformParams = typeof DisplacementVectorTransformParams;

export const DisplacementVectors3D = MSVTransform({
    name: "molsysviewer-displacement-vectors-3d",
    display: { name: "Displacement Vectors" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: DisplacementVectorTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Displacement Vectors", async ctx => {
            const repr = DisplacementVectorRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => DisplacementVectorParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Displacement Vectors", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

export interface DisplacementVectorOptions {
    origins?: Array<[number, number, number]>;
    atom_indices?: number[];
    vectors?: Array<[number, number, number]>;
    length_scale?: number;
    min_length?: number;
    max_length?: number;
    color_mode?: "norm" | "component";
    color_component?: number;
    color_map?: number[] | string;
    radius_scale?: number;
    radial_segments?: number;
    tag?: string;
}

function resolveOriginsFromAtoms(
    plugin: PluginContext,
    atomIndices: number[]
): Array<[number, number, number] | undefined> {
    const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
    const structure = structureRef?.cell.obj?.data as Structure | undefined;
    if (!structure) {
        console.warn("[MolSysViewer] add_displacement_vectors sin estructura cargada");
        return [];
    }

    const lookup = buildUnitLookup(structure);
    const position = Vec3();
    const origins: Array<[number, number, number] | undefined> = [];

    atomIndices.forEach((idx, pos) => {
        const loc = lookup.get(idx as ElementIndex);
        if (!loc) {
            console.warn(`[MolSysViewer] atom_indices[${pos}] no coincide con átomos de la estructura`);
            origins.push(undefined);
            return;
        }
        loc.unit.conformation.position(loc.elementIndex, position);
        origins.push([position[0], position[1], position[2]]);
    });

    return origins;
}

function prepareDisplacementVectorData(
    plugin: PluginContext,
    options: DisplacementVectorOptions
): DisplacementVectorData | undefined {
    const vectors = options.vectors ?? [];
    if (!vectors || vectors.length === 0) {
        console.warn("[MolSysViewer] add_displacement_vectors sin vectores");
        return undefined;
    }

    const origins = options.atom_indices && options.atom_indices.length > 0
        ? resolveOriginsFromAtoms(plugin, options.atom_indices)
        : options.origins ?? [];

    if (!origins || origins.length === 0) {
        console.warn("[MolSysViewer] add_displacement_vectors sin orígenes válidos");
        return undefined;
    }

    const count = Math.min(origins.length, vectors.length);
    if (count === 0) {
        console.warn("[MolSysViewer] add_displacement_vectors con longitudes incompatibles");
        return undefined;
    }

    const lengthScale = options.length_scale ?? 1;
    const minLength = options.min_length ?? 0;
    const maxLength = options.max_length ?? 0;
    const radialSegments = Math.max(3, Math.floor(options.radial_segments ?? 12));
    const radiusScale = options.radius_scale ?? 0.05;
    const colorMode: "norm" | "component" = options.color_mode ?? "norm";
    const colorComponent = Math.max(0, Math.min(2, Math.floor(options.color_component ?? 2)));

    const processed: { start: [number, number, number]; vector: Vec3; magnitude: number }[] = [];

    for (let i = 0; i < count; i++) {
        const origin = origins[i];
        const vec = vectors[i];
        if (!origin || !vec || origin.length !== 3 || vec.length !== 3) continue;

        const vector = Vec3.create(vec[0], vec[1], vec[2]);
        const magnitude = Vec3.magnitude(vector);
        if (magnitude < 1e-6) continue;

        processed.push({
            start: [Number(origin[0]), Number(origin[1]), Number(origin[2])],
            vector,
            magnitude,
        });
    }

    if (processed.length === 0) {
        console.warn("[MolSysViewer] add_displacement_vectors sin entradas utilizables");
        return undefined;
    }

    const scaledMax = Math.max(...processed.map(p => p.magnitude * lengthScale));
    const normalization = maxLength > 0 && scaledMax > maxLength ? maxLength / scaledMax : 1;

    const arrows: DisplacementArrowSpec[] = [];
    const colorValues: number[] = [];

    for (const entry of processed) {
        const scaledLength = entry.magnitude * lengthScale * normalization;
        if (scaledLength < minLength) continue;

        const direction = Vec3.scale(Vec3(), entry.vector, (lengthScale * normalization) / entry.magnitude);
        const start = Vec3.create(entry.start[0], entry.start[1], entry.start[2]);
        const end = Vec3.create(entry.start[0], entry.start[1], entry.start[2]);
        Vec3.add(end, end, direction);

        const value = colorMode === "component" ? entry.vector[colorComponent] : entry.magnitude;

        arrows.push({
            start: entry.start,
            end: [end[0], end[1], end[2]],
            length: scaledLength,
            value,
            color: ColorNames.gray,
        });
        colorValues.push(value);
    }

    if (arrows.length === 0) {
        console.warn("[MolSysViewer] add_displacement_vectors sin flechas tras filtrado");
        return undefined;
    }

    const minValue = Math.min(...colorValues);
    const maxValue = Math.max(...colorValues);
    const domain = minValue === maxValue ? [minValue, minValue + 1] : [minValue, maxValue];
    const palette = options.color_map && Array.isArray(options.color_map) && options.color_map.length === 0
        ? undefined
        : options.color_map;
    const scale = ColorScale.create({ domain, listOrName: palette ?? "turbo", minLabel: "min", maxLabel: "max" });

    arrows.forEach((arrow, idx) => {
        arrow.color = scale.color(colorValues[idx]);
    });

    const name = arrows.length === 1 ? "Displacement Vector" : `${arrows.length} Displacement Vectors`;

    return {
        arrows,
        radiusScale,
        radialSegments,
        name,
    };
}

export async function addDisplacementVectorsFromPython(
    plugin: PluginContext,
    options: DisplacementVectorOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | undefined> {
    const data = prepareDisplacementVectorData(plugin, options);
    if (!data) return undefined;

    const props: DisplacementVectorProps = {
        ...PD.getDefaultValues(DisplacementVectorParams),
    };

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        DisplacementVectors3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:displacement-vectors" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}
