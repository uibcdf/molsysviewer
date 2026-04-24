// src/shapes/index.ts

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
import { Mat4 } from "molstar/lib/mol-math/linear-algebra/3d/mat4";
import { addEllipsoid } from "molstar/lib/mol-geo/geometry/mesh/builder/ellipsoid";
import { Tensor } from "molstar/lib/mol-math/linear-algebra/tensor";

import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";

import { Structure, Unit, ElementIndex } from "molstar/lib/mol-model/structure";

import { Mesh } from "molstar/lib/mol-geo/geometry/mesh/mesh";
import { MeshBuilder } from "molstar/lib/mol-geo/geometry/mesh/mesh-builder";
import { addSphere } from "molstar/lib/mol-geo/geometry/mesh/builder/sphere";
import { addCylinder, BasicCylinderProps } from "molstar/lib/mol-geo/geometry/mesh/builder/cylinder";

import { Shape, ShapeGroup } from "molstar/lib/mol-model/shape";
import { ShapeRepresentation } from "molstar/lib/mol-repr/shape/representation";
import {
    Representation,
    RepresentationContext,
    RepresentationParamsGetter,
} from "molstar/lib/mol-repr/representation";
import { Transparency } from "molstar/lib/mol-theme/transparency";

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
// Pocket blob (Gaussian density from alpha-spheres)
// ------------------------------------------------------------------

export interface PocketBlobOptions {
    centers?: Array<[number, number, number]>;
    radii?: number[];
    radius_scale?: number;
    resolution?: number;
    iso_level?: number;
    iso_levels?: number[];
    iso_colors?: number[];
    iso_alphas?: number[];
    smoothing?: number;
    values?: number[];
    color_map?: number[] | string;
    alpha?: number;
    tag?: string;
    layer_tag?: string;
    name?: string;
}

interface PocketBlobData {
    mesh: Mesh;
    colors: Map<number, Color>;
    alpha: number;
    name: string;
}

const PocketBlobParams = {
    ...Mesh.Params,
};

type PocketBlobParams = typeof PocketBlobParams;
type PocketBlobProps = PD.Values<PocketBlobParams>;

function buildPocketBlobColors(count: number, values?: number[], colorMap?: number[] | string) {
    const colors = new Map<number, Color>();
    const base = Color(ColorNames.lightgrey);

    if (!values || values.length !== count) {
        for (let i = 0; i < count; i++) colors.set(i, base);
        return colors;
    }

    const min = Math.min(...values);
    const max = Math.max(...values);
    const domain = min === max ? [min, min + 1] : [min, max];
    const palette = Array.isArray(colorMap) && colorMap.length > 0 ? colorMap : undefined;
    const scale = ColorScale.create({ domain, listOrName: palette ?? "rainbow", minLabel: "min", maxLabel: "max" });

    values.forEach((v, idx) => {
        colors.set(idx, scale.color(v));
    });
    return colors;
}

function buildPocketBlobField(options: PocketBlobOptions) {
    const centers = options.centers ?? [];
    const radii = options.radii ?? [];
    if (centers.length === 0 || centers.length !== radii.length) {
        return void 0;
    }

    const radiusScale = Math.max(0.01, options.radius_scale ?? 1.0);
    const scaledRadii = radii.map(r => r * radiusScale);

    const smoothing = Math.max(0.1, options.smoothing ?? 1.0);
    const resolution = Math.max(0.25, options.resolution ?? 1.0);

    const min = Vec3.create(Number.POSITIVE_INFINITY, Number.POSITIVE_INFINITY, Number.POSITIVE_INFINITY);
    const max = Vec3.create(Number.NEGATIVE_INFINITY, Number.NEGATIVE_INFINITY, Number.NEGATIVE_INFINITY);

    let maxRadius = 0;
    centers.forEach((c, idx) => {
        const r = scaledRadii[idx];
        maxRadius = Math.max(maxRadius, r);
        Vec3.min(min, min, Vec3.create(c[0] - r * 2, c[1] - r * 2, c[2] - r * 2));
        Vec3.max(max, max, Vec3.create(c[0] + r * 2, c[1] + r * 2, c[2] + r * 2));
    });

    const padding = Math.max(resolution * 2, maxRadius * smoothing * 2);
    Vec3.sub(min, min, Vec3.create(padding, padding, padding));
    Vec3.add(max, max, Vec3.create(padding, padding, padding));

    const dims = Vec3();
    Vec3.sub(dims, max, min);
    const nX = Math.max(2, Math.ceil(dims[0] / resolution));
    const nY = Math.max(2, Math.ceil(dims[1] / resolution));
    const nZ = Math.max(2, Math.ceil(dims[2] / resolution));

    const space = Tensor.Space([nX, nY, nZ], [0, 1, 2], Float32Array);
    const scalarField = space.create() as Tensor.Data;

    const idSpace = Tensor.Space([nX, nY, nZ], [0, 1, 2], Int32Array);
    const idField = idSpace.create() as Tensor.Data;

    const sigmaFactor = smoothing;

    for (let k = 0; k < nZ; k++) {
        const z = min[2] + k * resolution;
        for (let j = 0; j < nY; j++) {
            const y = min[1] + j * resolution;
            for (let i = 0; i < nX; i++) {
                const x = min[0] + i * resolution;

                let density = 0;
                let best = -1;
                let bestVal = -Infinity;

                for (let s = 0; s < centers.length; s++) {
                    const c = centers[s];
                    const r = scaledRadii[s];
                    const dx = x - c[0];
                    const dy = y - c[1];
                    const dz = z - c[2];
                    const dist2 = dx * dx + dy * dy + dz * dz;
                    const sigma = Math.max(1e-3, r * sigmaFactor);
                    const val = Math.exp(-dist2 / (2 * sigma * sigma));
                    density += val;
                    if (val > bestVal) {
                        bestVal = val;
                        best = s;
                    }
                }

                space.set(scalarField, i, j, k, density);
                idSpace.set(idField, i, j, k, best);
            }
        }
    }

    return {
        scalarField: Tensor.create(space, scalarField),
        idField: Tensor.create(idSpace, idField),
        bottomLeft: [0, 0, 0] as [number, number, number],
        topRight: [nX, nY, nZ] as [number, number, number],
        count: centers.length,
        origin: [min[0], min[1], min[2]] as [number, number, number],
        resolution,
    };
}

function getPocketBlobShape(
    _ctx: RuntimeContext,
    data: PocketBlobData,
    _props: PocketBlobProps,
    shape?: Shape<Mesh>
) {
    const getColor = (groupId: number) => data.colors.get(groupId) ?? Color(ColorNames.lightgrey);
    const getSize = () => 1;
    const getLabel = (groupId: number) => `${data.name} (region ${groupId})`;
    return Shape.create(data.name, data, data.mesh, getColor, getSize, getLabel, shape?.transforms);
}

const PocketBlobVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<PocketBlobData, PocketBlobParams>
    ) => ShapeRepresentation(getPocketBlobShape, Mesh.Utils),
};

type PocketBlobRepresentation = Representation<PocketBlobData, PocketBlobParams>;

function PocketBlobRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<PocketBlobData, PocketBlobParams>
): PocketBlobRepresentation {
    return Representation.createMulti(
        "PocketBlob",
        ctx,
        getParams,
        Representation.StateBuilder,
        PocketBlobVisuals as unknown as Representation.Def<PocketBlobData, PocketBlobParams>
    );
}

const PocketBlobTransformParams = {
    data: PD.Value<PocketBlobData>(undefined as any),
    props: PD.Value<PocketBlobProps>(undefined as any),
};

type PocketBlobTransformParams = typeof PocketBlobTransformParams;

export const PocketBlob3D = MSVTransform({
    name: "molsysviewer-pocket-blob-3d",
    display: { name: "Pocket Blob" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: PocketBlobTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Pocket Blob", async ctx => {
            const repr = PocketBlobRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => PocketBlobParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: params.data.alpha });

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Pocket Blob", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.data.alpha });
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

function preparePocketBlobData(options: PocketBlobOptions): Array<PocketBlobData & { transform: Mat4 }> | undefined {
    const field = buildPocketBlobField(options);
    if (!field) {
        console.warn("[MolSysViewer] add_pocket_blob: no valid data");
        return undefined;
    }

    const levels = options.iso_levels && options.iso_levels.length > 0 ? options.iso_levels : [options.iso_level ?? 0.1];
    const baseAlpha = options.alpha ?? 0.5;
    const isoAlphas = options.iso_alphas && options.iso_alphas.length === levels.length
        ? options.iso_alphas
        : new Array(levels.length).fill(baseAlpha);

    const isoColors = options.iso_colors && options.iso_colors.length === levels.length
        ? options.iso_colors
        : undefined;

    const colorScale = !isoColors ? ColorScale.create({ domain: [Math.min(...levels), Math.max(...levels)], listOrName: options.color_map ?? "turbo" }) : undefined;

    const results: Array<PocketBlobData & { transform: Mat4 }> = [];
    levels.forEach((level, idx) => {
        const isoColor = isoColors ? isoColors[idx] : colorScale?.color(level);
        const regionColors = isoColor !== undefined
            ? new Map<number, Color>(Array.from({ length: field.count }, (_v, i) => [i, isoColor]))
            : buildPocketBlobColors(field.count, options.values, options.color_map);

        const mesh = computeMarchingCubesMesh({
            isoLevel: level,
            scalarField: field.scalarField,
            idField: field.idField,
            bottomLeft: field.bottomLeft,
            topRight: field.topRight,
        });

        const transform = Mat4.identity();
        Mat4.fromScaling(transform, Vec3.create(field.resolution, field.resolution, field.resolution));
        Mat4.setTranslation(transform, Vec3.create(field.origin[0], field.origin[1], field.origin[2]));

        results.push({
            mesh,
            colors: regionColors,
            alpha: isoAlphas[idx],
            name: `${options.name ?? "Pocket Blob"} (iso=${level})`,
            transform,
        });
    });

    return results;
}

export async function addPocketBlobFromPython(
    plugin: PluginContext,
    options: PocketBlobOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | StateObjectRef<SO.Shape.Representation3D>[] | undefined> {
    const datasets = preparePocketBlobData(options);
    if (!datasets) return undefined;

    const props: PocketBlobProps = {
        ...PD.getDefaultValues(PocketBlobParams),
    };

    const refs: StateObjectRef<SO.Shape.Representation3D>[] = [];

    for (const data of datasets) {
        const blobMesh = await plugin.runTask(data.mesh);
        Mesh.transform(blobMesh, data.transform);

        const builder = plugin.state.data.build();
        const node = builder.toRoot().apply(
            PocketBlob3D,
            {
                data: { ...data, mesh: blobMesh },
                props,
            } as any,
            { tags: options.tag ?? "molsysviewer:pocket-blob" }
        );

        await PluginCommands.State.Update(plugin, {
            state: plugin.state.data,
            tree: builder,
            options: { doNotLogTiming: true },
        });

        refs.push(node.ref as StateObjectRef<SO.Shape.Representation3D>);
    }

    return refs.length === 1 ? refs[0] : refs;
}

// ------------------------------------------------------------------
// Channel tube (swept cylinders along ordered centers)
// ------------------------------------------------------------------

type ChannelColorMode = "segment" | "solvent";

export interface ChannelTubeOptions {
    centers?: Array<[number, number, number]>;
    radii?: number[];
    solvent_distances?: number[];
    colors?: number[];
    palette?: number[] | string;
    color_map?: number[] | string;
    color_by?: ChannelColorMode;
    color_mode?: ChannelColorMode;
    radial_segments?: number;
    smoothing_subdivisions?: number;
    alpha?: number;
    tag?: string;
    layer_tag?: string;
    name?: string;
    structures_coords?: Array<Array<[number, number, number]> | null>;
}

interface ChannelSegment {
    start: [number, number, number];
    end: [number, number, number];
    radius: number;
    color: number;
}

interface ChannelTubeData {
    segments: ChannelSegment[];
    alpha: number;
    name: string;
}

const ChannelTubeParams = {
    ...Mesh.Params,
    radialSegments: PD.Numeric(16, { min: 3, max: 64, step: 1 }),
};

type ChannelTubeParams = typeof ChannelTubeParams;
type ChannelTubeProps = PD.Values<ChannelTubeParams>;

function catmullRomPoint(p0: Vec3, p1: Vec3, p2: Vec3, p3: Vec3, t: number, out: Vec3) {
    const t2 = t * t;
    const t3 = t2 * t;
    out[0] = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3);
    out[1] = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3);
    out[2] = 0.5 * ((2 * p1[2]) + (-p0[2] + p2[2]) * t + (2 * p0[2] - 5 * p1[2] + 4 * p2[2] - p3[2]) * t2 + (-p0[2] + 3 * p1[2] - 3 * p2[2] + p3[2]) * t3);
    return out;
}

function buildChannelSegments(options: ChannelTubeOptions): { segments: ChannelSegment[]; radialSegments: number } {
    const centers = options.centers ?? [];
    const radii = options.radii ?? [];
    if (centers.length < 2 || centers.length !== radii.length) return { segments: [], radialSegments: 16 };

    const subdiv = Math.max(0, Math.floor(options.smoothing_subdivisions ?? 0));
    const points: Vec3[] = centers.map(c => Vec3.create(c[0], c[1], c[2]));
    const radiiList = radii.map(r => Math.max(0.01, r));
    const distanceList = options.solvent_distances ? options.solvent_distances.slice() : void 0;

    if (subdiv > 0 && points.length >= 4) {
        const refined: Vec3[] = [];
        const refinedRadii: number[] = [];
        const refinedDistances: number[] = [];
        const steps = subdiv + 1;
        for (let i = 0; i < points.length - 1; i++) {
            const p0 = points[Math.max(0, i - 1)];
            const p1 = points[i];
            const p2 = points[i + 1];
            const p3 = points[Math.min(points.length - 1, i + 2)];

            const r0 = radiiList[Math.max(0, i - 1)];
            const r1 = radiiList[i];
            const r2 = radiiList[i + 1];
            const r3 = radiiList[Math.min(points.length - 1, i + 2)];

            const d0 = distanceList && distanceList[Math.max(0, i - 1)];
            const d1 = distanceList && distanceList[i];
            const d2 = distanceList && distanceList[i + 1];
            const d3 = distanceList && distanceList[Math.min(points.length - 1, i + 2)];

            for (let s = 0; s < steps; s++) {
                const t = s / steps;
                const v = Vec3();
                catmullRomPoint(p0, p1, p2, p3, t, v);
                refined.push(v);
                const r = 0.5 * ((r1 + r2) + t * (r2 - r1) + t * t * (r0 - 2 * r1 + r2) + t * t * t * (-r0 + 3 * r1 - 3 * r2 + r3));
                refinedRadii.push(Math.max(0.01, r));
                if (distanceList && d0 !== undefined && d1 !== undefined && d2 !== undefined && d3 !== undefined) {
                    const dt = 0.5 * ((d1 + d2) + t * (d2 - d1) + t * t * (d0 - 2 * d1 + d2) + t * t * t * (-d0 + 3 * d1 - 3 * d2 + d3));
                    refinedDistances.push(dt);
                }
            }
        }
        points.splice(0, points.length, ...refined);
        radiiList.splice(0, radiiList.length, ...refinedRadii);
        if (distanceList && refinedDistances.length === refined.length) {
            distanceList.splice(0, distanceList.length, ...refinedDistances);
        }
    }

    const colorMode: ChannelColorMode = options.color_by ?? options.color_mode ?? "segment";
    const radialSegments = Math.max(3, Math.floor(options.radial_segments ?? 16));
    const colors = options.colors;
    const solventDistances = distanceList ?? options.solvent_distances;
    const colorMap = options.palette ?? options.color_map;

    const segments: ChannelSegment[] = [];

    const palette = [
        ColorNames.blue,
        ColorNames.orange,
        ColorNames.green,
        ColorNames.red,
        ColorNames.purple,
        ColorNames.gray,
        ColorNames.pink,
        ColorNames.brown,
    ];

    let distanceScale: ColorScale | undefined;
    if (colorMode === "solvent" && solventDistances && solventDistances.length === radiiList.length) {
        const min = Math.min(...solventDistances);
        const max = Math.max(...solventDistances);
        const domain = min === max ? [min, min + 1] : [min, max];
        distanceScale = ColorScale.create({ domain, listOrName: colorMap ?? "turbo" });
    }

    for (let i = 0; i < points.length - 1; i++) {
        const start = points[i];
        const end = points[i + 1];
        const radius = (radiiList[i] + radiiList[i + 1]) * 0.5;

        let color = ColorNames.skyblue;
        if (colorMode === "segment") {
            if (colors && colors.length) {
                color = colors[i % colors.length];
            } else {
                color = palette[i % palette.length];
            }
        } else if (colorMode === "solvent" && distanceScale && solventDistances && solventDistances.length === radiiList.length) {
            const v1 = solventDistances[Math.min(solventDistances.length - 1, i)];
            const v2 = solventDistances[Math.min(solventDistances.length - 1, i + 1)];
            color = distanceScale.color((v1 + v2) * 0.5);
        }

        segments.push({
            start: [start[0], start[1], start[2]],
            end: [end[0], end[1], end[2]],
            radius,
            color,
        });
    }

    return { segments, radialSegments };
}

function buildChannelTubeMesh(data: { segments: ChannelSegment[]; radialSegments: number }, _props: ChannelTubeProps, prev?: Mesh) {
    const state = MeshBuilder.createState(512, 256, prev);
    const start = Vec3();
    const end = Vec3();

    data.segments.forEach((seg, idx) => {
        state.currentGroup = idx;
        Vec3.set(start, seg.start[0], seg.start[1], seg.start[2]);
        Vec3.set(end, seg.end[0], seg.end[1], seg.end[2]);
        const props: BasicCylinderProps = {
            radiusTop: seg.radius,
            radiusBottom: seg.radius,
            radialSegments: Math.max(3, data.radialSegments),
        };
        addCylinder(state, start, end, 1, props);
    });

    return MeshBuilder.getMesh(state);
}

function getChannelTubeShape(
    _ctx: RuntimeContext,
    data: ChannelTubeData,
    _props: ChannelTubeProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildChannelTubeMesh(
        { segments: data.segments, radialSegments: (_props as any).radialSegments ?? 16 },
        _props,
        shape?.geometry
    );
    const getColor = (groupId: number) => Color(data.segments[groupId].color);
    const getSize = (groupId: number) => data.segments[groupId].radius;
    const getLabel = (groupId: number) => `${data.name} ${groupId}`;

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const ChannelTubeVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<ChannelTubeData, ChannelTubeParams>
    ) => ShapeRepresentation(getChannelTubeShape, Mesh.Utils),
};

type ChannelTubeRepresentation = Representation<ChannelTubeData, ChannelTubeParams>;

function ChannelTubeRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<ChannelTubeData, ChannelTubeParams>
): ChannelTubeRepresentation {
    return Representation.createMulti(
        "ChannelTube",
        ctx,
        getParams,
        Representation.StateBuilder,
        ChannelTubeVisuals as unknown as Representation.Def<ChannelTubeData, ChannelTubeParams>
    );
}

const ChannelTubeTransformParams = {
    data: PD.Value<ChannelTubeData>(undefined as any),
    props: PD.Value<ChannelTubeProps>(undefined as any),
};

type ChannelTubeTransformParams = typeof ChannelTubeTransformParams;

export const ChannelTube3D = MSVTransform({
    name: "molsysviewer-channel-tube-3d",
    display: { name: "Channel Tube" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: ChannelTubeTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Channel Tube", async ctx => {
            const repr = ChannelTubeRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => ChannelTubeParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: params.data.alpha });

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Channel Tube", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.data.alpha });
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

function prepareChannelTubeData(options: ChannelTubeOptions): { data?: ChannelTubeData; radialSegments: number } {
    const built = buildChannelSegments(options);
    const segments = built.segments;
    if (!segments || segments.length === 0) {
        console.warn("[MolSysViewer] add_channel_tube: no valid segments");
        return { radialSegments: built.radialSegments };
    }

    const alpha = options.alpha ?? 1.0;
    const name = options.name ?? "Channel Tube";
    const radialSegments = built.radialSegments;

    return {
        data: {
            segments,
            alpha,
            name,
        },
        radialSegments,
    };
}

export async function addChannelTubeFromPython(
    plugin: PluginContext,
    options: ChannelTubeOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | undefined> {
    const { data, radialSegments } = prepareChannelTubeData(options);
    if (!data) return undefined;

    const props: ChannelTubeProps = {
        ...PD.getDefaultValues(ChannelTubeParams),
        radialSegments,
    } as any;

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        ChannelTube3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:channel-tube" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}

// ------------------------------------------------------------------
// Anisotropy ellipsoids / discs
// ------------------------------------------------------------------

type EllipsoidColorMode = "anisotropy" | "fixed";

export interface AnisotropyEllipsoidOptions {
    centers?: Array<[number, number, number]>;
    atom_indices?: number[];
    eigenvalues?: Array<[number, number, number]>;
    eigenvectors?: Array<[[number, number, number], [number, number, number], [number, number, number]]>;
    tensors?: Array<[[number, number, number], [number, number, number], [number, number, number]]>;
    principal_directions?: Array<[number, number, number]>;
    scale?: number;
    max_eccentricity?: number;
    color_by?: EllipsoidColorMode;
    palette?: number[] | string;
    color_mode?: EllipsoidColorMode;
    color_map?: number[] | string;
    colors?: number[];
    values?: number[];
    alpha?: number;
    tag?: string;
    layer_tag?: string;
    name?: string;
}

interface EllipsoidSpec {
    center: [number, number, number];
    axes: [number, number, number];
    dirA: Vec3;
    dirB: Vec3;
    color: number;
}

interface AnisotropyEllipsoidData {
    ellipsoids: EllipsoidSpec[];
    alpha: number;
    name: string;
}

const AnisotropyEllipsoidParams = {
    ...Mesh.Params,
};

type AnisotropyEllipsoidParams = typeof AnisotropyEllipsoidParams;
type AnisotropyEllipsoidProps = PD.Values<AnisotropyEllipsoidParams>;

function clampEccentricity(axes: [number, number, number], maxEcc?: number) {
    if (!maxEcc || maxEcc <= 1) return axes;
    const [a, b, c] = axes;
    const maxVal = Math.max(a, b, c);
    const minAllowed = maxVal / maxEcc;
    return [
        Math.max(a, minAllowed),
        Math.max(b, minAllowed),
        Math.max(c, minAllowed),
    ] as [number, number, number];
}

function anisotropyValue(axes: [number, number, number]) {
    const maxVal = Math.max(...axes);
    const minVal = Math.min(...axes);
    if (maxVal <= 0) return 0;
    return (maxVal - minVal) / maxVal;
}

function normalizeVec(v: [number, number, number]): Vec3 {
    const out = Vec3.create(v[0], v[1], v[2]);
    Vec3.normalize(out, out);
    return out;
}

function fallbackDirs(): [Vec3, Vec3] {
    return [Vec3.create(1, 0, 0), Vec3.create(0, 1, 0)];
}

function buildEllipsoidSpecs(
    plugin: PluginContext,
    options: AnisotropyEllipsoidOptions
): EllipsoidSpec[] {
    const centers = options.centers ? [...options.centers] : [];
    if (centers.length === 0 && options.atom_indices) {
        const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
        const structure = structureRef?.cell.obj?.data as Structure | undefined;
        if (structure) {
            const lookup = buildUnitLookup(structure);
            options.atom_indices.forEach(idx => {
                const loc = lookup.get(idx as ElementIndex);
                if (loc) {
                    const p = Vec3();
                    loc.unit.conformation.position(loc.elementIndex, p);
                    centers.push([p[0], p[1], p[2]]);
                }
            });
        }
    }

    const n = centers.length;
    if (n === 0) return [];

    const scale = options.scale ?? 1;
    const maxEcc = options.max_eccentricity ?? 0;

    const specs: EllipsoidSpec[] = [];
    const colorMode: EllipsoidColorMode = options.color_by ?? options.color_mode ?? "anisotropy";
    const values = options.values;
    const colors = options.colors;
    const colorMap = options.palette ?? options.color_map;

    let scaleLookup: ColorScale | undefined;
    if (colorMode === "anisotropy") {
        scaleLookup = ColorScale.create({ domain: [0, 1], listOrName: colorMap ?? "turbo" });
    }

    for (let i = 0; i < n; i++) {
        const center = centers[i];

        const eigenVals = options.eigenvalues?.[i];
        const eigenVecs = options.eigenvectors?.[i]?.map(v => normalizeVec(v as any)) as [Vec3, Vec3, Vec3] | undefined;
        const tensor = options.tensors?.[i];
        const principal = options.principal_directions?.[i];

        let axes: [number, number, number] | undefined;
        let dirA: Vec3 | undefined;
        let dirB: Vec3 | undefined;

        if (eigenVals && eigenVecs) {
            axes = [Math.abs(eigenVals[0]), Math.abs(eigenVals[1]), Math.abs(eigenVals[2])];
            dirA = eigenVecs[0];
            dirB = eigenVecs[1];
        } else if (principal) {
            axes = [1, 0.2, 0.2];
            dirA = normalizeVec(principal as any);
            dirB = Vec3.orthogonal(Vec3(), dirA);
        } else if (tensor && tensor.length === 3) {
            axes = [
                Math.abs(tensor[0][0]),
                Math.abs(tensor[1][1]),
                Math.abs(tensor[2][2]),
            ];
            const [a, b] = fallbackDirs();
            dirA = a;
            dirB = b;
        } else {
            continue;
        }

        axes = clampEccentricity([
            axes[0] * scale,
            axes[1] * scale,
            axes[2] * scale,
        ], maxEcc);

        const anisotropy = anisotropyValue(axes);
        let color = ColorNames.orange;
        if (colorMode === "fixed" && colors && colors.length) {
            color = colors[i % colors.length];
        } else if (colorMode === "anisotropy" && scaleLookup) {
            color = scaleLookup.color(values?.[i] ?? anisotropy);
        } else if (colors && colors.length) {
            color = colors[i % colors.length];
        }

        const [fallbackA, fallbackB] = fallbackDirs();
        specs.push({
            center: [center[0], center[1], center[2]],
            axes: axes,
            dirA: dirA ?? fallbackA,
            dirB: dirB ?? fallbackB,
            color,
        });
    }

    return specs;
}

function buildAnisotropyEllipsoidMesh(data: AnisotropyEllipsoidData, _props: AnisotropyEllipsoidProps, prev?: Mesh) {
    const state = MeshBuilder.createState(256, 128, prev);
    const detail = 2;
    data.ellipsoids.forEach((ellipsoid, idx) => {
        state.currentGroup = idx;
        addEllipsoid(
            state,
            Vec3.create(ellipsoid.center[0], ellipsoid.center[1], ellipsoid.center[2]),
            ellipsoid.dirA,
            ellipsoid.dirB,
            Vec3.create(ellipsoid.axes[0], ellipsoid.axes[1], ellipsoid.axes[2]),
            detail
        );
    });
    return MeshBuilder.getMesh(state);
}

function getAnisotropyEllipsoidShape(
    _ctx: RuntimeContext,
    data: AnisotropyEllipsoidData,
    _props: AnisotropyEllipsoidProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildAnisotropyEllipsoidMesh(data, _props, shape?.geometry);
    const getColor = (groupId: number) => Color(data.ellipsoids[groupId].color);
    const getSize = (groupId: number) => data.ellipsoids[groupId].axes[0];
    const getLabel = (groupId: number) => `${data.name} ${groupId}`;

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const AnisotropyEllipsoidVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<AnisotropyEllipsoidData, AnisotropyEllipsoidParams>
    ) => ShapeRepresentation(getAnisotropyEllipsoidShape, Mesh.Utils),
};

type AnisotropyEllipsoidRepresentation = Representation<AnisotropyEllipsoidData, AnisotropyEllipsoidParams>;

function AnisotropyEllipsoidRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<AnisotropyEllipsoidData, AnisotropyEllipsoidParams>
): AnisotropyEllipsoidRepresentation {
    return Representation.createMulti(
        "AnisotropyEllipsoids",
        ctx,
        getParams,
        Representation.StateBuilder,
        AnisotropyEllipsoidVisuals as unknown as Representation.Def<AnisotropyEllipsoidData, AnisotropyEllipsoidParams>
    );
}

const AnisotropyEllipsoidTransformParams = {
    data: PD.Value<AnisotropyEllipsoidData>(undefined as any),
    props: PD.Value<AnisotropyEllipsoidProps>(undefined as any),
};

type AnisotropyEllipsoidTransformParams = typeof AnisotropyEllipsoidTransformParams;

export const AnisotropyEllipsoids3D = MSVTransform({
    name: "molsysviewer-anisotropy-ellipsoids-3d",
    display: { name: "Anisotropy Ellipsoids" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: AnisotropyEllipsoidTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Anisotropy Ellipsoids", async ctx => {
            const repr = AnisotropyEllipsoidRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => AnisotropyEllipsoidParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: params.data.alpha });

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Anisotropy Ellipsoids", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.data.alpha });
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

function prepareAnisotropyEllipsoidData(
    plugin: PluginContext,
    options: AnisotropyEllipsoidOptions
): AnisotropyEllipsoidData | undefined {
    const ellipsoids = buildEllipsoidSpecs(plugin, options);
    if (ellipsoids.length === 0) {
        console.warn("[MolSysViewer] add_anisotropy_ellipsoids: no valid data");
        return undefined;
    }

    const alpha = options.alpha ?? 0.6;
    const name = options.name ?? "Anisotropy Ellipsoids";

    return {
        ellipsoids,
        alpha,
        name,
    };
}

export async function addAnisotropyEllipsoidsFromPython(
    plugin: PluginContext,
    options: AnisotropyEllipsoidOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | undefined> {
    const data = prepareAnisotropyEllipsoidData(plugin, options);
    if (!data) return undefined;

    const props: AnisotropyEllipsoidProps = {
        ...PD.getDefaultValues(AnisotropyEllipsoidParams),
    };

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        AnisotropyEllipsoids3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:anisotropy-ellipsoids" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}

// ------------------------------------------------------------------
// Pharmacophore features (basic glyphs)
// ------------------------------------------------------------------

type PharmKind = "donor" | "acceptor" | "hydrophobe" | "aromatic" | "positive" | "negative" | "metal";

export interface PharmacophoreOptions {
    centers?: Array<[number, number, number]>;
    kinds?: PharmKind[] | string[];
    radii?: number[];
    alphas?: number[];
    directions?: Array<[number, number, number]>;
    colors?: number[];
    color_scheme?: string;
    color_table?: Record<string, number>;
    tag?: string;
    layer_tag?: string;
    name?: string;
}

interface PharmacophoreGlyph {
    center: [number, number, number];
    radius: number;
    alpha: number;
    color: number;
    kind: string;
    direction?: [number, number, number];
}

interface PharmacophoreData {
    glyphs: PharmacophoreGlyph[];
    name: string;
}

const PharmColors: Record<string, number> = {
    donor: 0x3b82f6,
    acceptor: 0xef4444,
    hydrophobe: 0xf59e0b,
    aromatic: 0x8b5cf6,
    positive: 0x2563eb,
    negative: 0xf43f5e,
    metal: 0x10b981,
};

const PharmacophoreParams = {
    ...Mesh.Params,
};

type PharmacophoreParams = typeof PharmacophoreParams;
type PharmacophoreProps = PD.Values<PharmacophoreParams>;

function buildPharmacophoreMesh(data: PharmacophoreData, _props: PharmacophoreProps, prev?: Mesh): Mesh {
    const state = MeshBuilder.createState(256, 128, prev);
    const center = Vec3();
    const dir = Vec3();
    const tip = Vec3();
    const base = Vec3();

    data.glyphs.forEach((g, idx) => {
        state.currentGroup = idx;
        Vec3.set(center, g.center[0], g.center[1], g.center[2]);
        addSphere(state, center, g.radius, 2);

        if (g.direction) {
            Vec3.set(dir, g.direction[0], g.direction[1], g.direction[2]);
            if (Vec3.magnitude(dir) > 1e-6) {
                Vec3.normalize(dir, dir);
                Vec3.scale(tip, dir, g.radius * 2.0);
                Vec3.add(tip, center, tip);
                Vec3.scale(base, dir, g.radius * 1.2);
                Vec3.add(base, center, base);
                addCylinder(state, center, base, 1, { radiusTop: g.radius * 0.3, radiusBottom: g.radius * 0.3, radialSegments: 10 });
                addCylinder(state, base, tip, g.radius * 0.6, {
                    topCap: true,
                    bottomCap: true,
                    radialSegments: 12,
                });
            }
        }
    });

    return MeshBuilder.getMesh(state);
}

function getPharmacophoreShape(
    _ctx: RuntimeContext,
    data: PharmacophoreData,
    _props: PharmacophoreProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildPharmacophoreMesh(data, _props, shape?.geometry);
    const getColor = (groupId: number) => Color(data.glyphs[groupId].color);
    const getSize = (groupId: number) => data.glyphs[groupId].radius;
    const getLabel = (groupId: number) => `${data.glyphs[groupId].kind}`;

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const PharmacophoreVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<PharmacophoreData, PharmacophoreParams>
    ) => ShapeRepresentation(getPharmacophoreShape, Mesh.Utils),
};

type PharmacophoreRepresentation = Representation<PharmacophoreData, PharmacophoreParams>;

function PharmacophoreRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<PharmacophoreData, PharmacophoreParams>
): PharmacophoreRepresentation {
    return Representation.createMulti(
        "PharmacophoreFeatures",
        ctx,
        getParams,
        Representation.StateBuilder,
        PharmacophoreVisuals as unknown as Representation.Def<PharmacophoreData, PharmacophoreParams>
    );
}

const PharmacophoreTransformParams = {
    data: PD.Value<PharmacophoreData>(undefined as any),
    props: PD.Value<PharmacophoreProps>(undefined as any),
};

type PharmacophoreTransformParams = typeof PharmacophoreTransformParams;

export const Pharmacophore3D = MSVTransform({
    name: "molsysviewer-pharmacophore-3d",
    display: { name: "Pharmacophore Features" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: PharmacophoreTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Pharmacophore Features", async ctx => {
            const repr = PharmacophoreRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => PharmacophoreParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: 1 });

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Pharmacophore Features", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

function preparePharmacophoreData(options: PharmacophoreOptions): PharmacophoreData | undefined {
    const centers = options.centers ?? [];
    const kinds = options.kinds ?? [];
    if (centers.length === 0 || centers.length !== kinds.length) {
        console.warn("[MolSysViewer] add_pharmacophore_features requires centers and kinds of the same length");
        return undefined;
    }

    const radii = options.radii && options.radii.length === centers.length
        ? options.radii
        : new Array(centers.length).fill(0.6);
    const alphas = options.alphas && options.alphas.length === centers.length
        ? options.alphas
        : new Array(centers.length).fill(0.6);
    const colorTable = options.color_table;
    const colorScheme = options.color_scheme;
    const schemeLookup = colorScheme === "pharmacophore_default" || colorScheme === undefined
        ? PharmColors
        : PharmColors;
    const colors = options.colors && options.colors.length === centers.length
        ? options.colors
        : kinds.map(k => colorTable?.[k.toLowerCase()] ?? schemeLookup[k.toLowerCase()] ?? ColorNames.gray);
    const directions = options.directions;

    const glyphs: PharmacophoreGlyph[] = centers.map((c, i) => ({
        center: [c[0], c[1], c[2]],
        radius: radii[i],
        alpha: alphas[i],
        color: colors[i],
        kind: kinds[i],
        direction: directions?.[i],
    }));

    const name = options.name ?? "Pharmacophore Features";

    return { glyphs, name };
}

export async function addPharmacophoreFromPython(
    plugin: PluginContext,
    options: PharmacophoreOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | undefined> {
    const data = preparePharmacophoreData(options);
    if (!data) return undefined;

    const props: PharmacophoreProps = {
        ...PD.getDefaultValues(PharmacophoreParams),
    };

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        Pharmacophore3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:pharmacophore" }
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
    color_by?: NetworkLinkColorMode;
    color_scheme?: string;
    color_table?: Record<string, number>;
    color_mode?: NetworkLinkColorMode;
    alpha?: number;
    radial_segments?: number;
    tag?: string;
    layer_tag?: string;
    structures_coords?: Array<CoordinatePair[] | null>;
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
        console.warn(`[MolSysViewer] Expected ${count} values but got ${value.length}. The first value will be reused.`);
        return Array(count).fill(cast(value[0]));
    }
    return Array(count).fill(cast((value ?? fallback) as T));
}

function normalizeCategoryKey(key: string | number | undefined): string | undefined {
    if (key === undefined) return undefined;
    return String(key);
}

function prepareColorLookup(keys: Array<string | number>, fallback: number, colorTable?: Record<string, number>) {
    if (colorTable) {
        return (key?: string | number) => {
            const normalized = normalizeCategoryKey(key);
            return normalized !== undefined ? colorTable[normalized] ?? fallback : fallback;
        };
    }
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
    const colorMode: NetworkLinkColorMode = options.color_by ?? options.color_mode ?? "link";
    const colors = expandToList<number>(options.colors, count, Number, ColorNames.skyblue);
    const colorTable = options.color_table;

    const paletteLookup = prepareColorLookup(colorMode === "pocket" ? pocketIds : chainIds, colors[0], colorTable);

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
    const colorMode: NetworkLinkColorMode = options.color_by ?? options.color_mode ?? "link";
    const colors = expandToList<number>(options.colors, count, Number, ColorNames.skyblue);
    const colorTable = options.color_table;

    const positionsStart = Vec3();
    const positionsEnd = Vec3();

    const chainIdList: string[] = [];
    const specs: NetworkLinkSpec[] = [];

    for (let i = 0; i < count; i++) {
        const [a, b] = pairs[i];
        const locA = lookup.get(a as ElementIndex);
        const locB = lookup.get(b as ElementIndex);
        if (!locA || !locB) {
            console.warn(`[MolSysViewer] atom_pairs[${i}] does not match atoms in the structure`);
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
        const paletteLookup = prepareColorLookup(chainIdList, colors[0], colorTable);
        specs.forEach((spec, idx) => {
            spec.color = paletteLookup(chainIdList[idx]);
        });
    } else if (colorMode === "pocket") {
        const paletteLookup = prepareColorLookup(pocketIds, colors[0], colorTable);
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
            console.warn("[MolSysViewer] add_network_links: no structure loaded");
            return undefined;
        }
        links = buildLinksFromAtoms(structure, options);
        name = getNetworkLinksName(links.length);
    } else {
        links = buildLinksFromCoordinates(options);
        name = getNetworkLinksName(links.length);
    }

    if (links.length === 0) {
        console.warn("[MolSysViewer] add_network_links: no valid data");
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
    edges?: {
        enabled: boolean;
        radius: number;
        color: number;
    };
    normals?: {
        enabled: boolean;
        length: number;
        color: number;
        radius: number;
    };
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
    const edgeStart = Vec3();
    const edgeEnd = Vec3();
    const centroid = Vec3();
    const ab = Vec3();
    const ac = Vec3();
    const normal = Vec3();

    const edgeRadius = data.edges?.radius ?? 0.05;
    const normalLength = data.normals?.length ?? 0.5;
    const normalRadius = data.normals?.radius ?? edgeRadius * 0.6;

    let groupIndex = 0;
    for (let i = 0, il = data.triangles.length; i < il; i++) {
        const tri = data.triangles[i];
        state.currentGroup = groupIndex++;
        Vec3.set(a, tri.vertices[0][0], tri.vertices[0][1], tri.vertices[0][2]);
        Vec3.set(b, tri.vertices[1][0], tri.vertices[1][1], tri.vertices[1][2]);
        Vec3.set(c, tri.vertices[2][0], tri.vertices[2][1], tri.vertices[2][2]);
        MeshBuilder.addTriangle(state, a, b, c);

        // Opcional: wireframe de aristas
        if (data.edges?.enabled) {
            const r = edgeRadius;
            Vec3.copy(edgeStart, a);
            Vec3.copy(edgeEnd, b);
            state.currentGroup = groupIndex++;
            addCylinder(state, edgeStart, edgeEnd, 1, { radiusTop: r, radiusBottom: r, radialSegments: 8 });
            Vec3.copy(edgeStart, b);
            Vec3.copy(edgeEnd, c);
            state.currentGroup = groupIndex++;
            addCylinder(state, edgeStart, edgeEnd, 1, { radiusTop: r, radiusBottom: r, radialSegments: 8 });
            Vec3.copy(edgeStart, c);
            Vec3.copy(edgeEnd, a);
            state.currentGroup = groupIndex++;
            addCylinder(state, edgeStart, edgeEnd, 1, { radiusTop: r, radiusBottom: r, radialSegments: 8 });
        }

        // Opcional: flechas de normales por cara
        if (data.normals?.enabled) {
            Vec3.sub(ab, b, a);
            Vec3.sub(ac, c, a);
            Vec3.cross(normal, ab, ac);
            if (Vec3.magnitude(normal) > 1e-6) {
                Vec3.normalize(normal, normal);
                Vec3.scale(normal, normal, normalLength);
                Vec3.scaleAndAdd(centroid, a, b, 1);
                Vec3.add(centroid, centroid, c);
                Vec3.scale(centroid, centroid, 1 / 3);

                const arrowTip = Vec3();
                Vec3.add(arrowTip, centroid, normal);

                const shaftRadius = normalRadius;
                const headRadius = shaftRadius * 1.8;
                const shaftLength = normalLength * 0.7;
                const headStart = Vec3();
                Vec3.scaleAndAdd(headStart, centroid, normal, shaftLength / normalLength);

                state.currentGroup = groupIndex++;
                addCylinder(state, centroid, headStart, 1, { radiusTop: shaftRadius, radiusBottom: shaftRadius, radialSegments: 12 });
                addCylinder(state, headStart, arrowTip, 1, { radiusTop: 0.0001, radiusBottom: headRadius, radialSegments: 12 });
            }
        }
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
    const triCount = data.triangles.length;
    const edgesEnabled = !!data.edges?.enabled;
    const normalsEnabled = !!data.normals?.enabled;
    const edgesPerTri = edgesEnabled ? 3 : 0;
    const getColor = (groupId: number) => {
        if (groupId < triCount) {
            return Color(data.triangles[groupId].color);
        }
        let offset = groupId - triCount;
        if (edgesEnabled) {
            const totalEdges = triCount * edgesPerTri;
            if (offset < totalEdges) {
                return Color(data.edges?.color ?? ColorNames.black);
            }
            offset -= totalEdges;
        }
        if (normalsEnabled) {
            return Color(data.normals?.color ?? ColorNames.red);
        }
        return Color(ColorNames.gray);
    };
    const getSize = () => 1;
    const getLabel = (groupId: number) => {
        if (groupId < triCount) {
            return data.triangles[groupId].label ?? `Triangle ${groupId}`;
        }
        let offset = groupId - triCount;
        if (edgesEnabled) {
            const totalEdges = triCount * edgesPerTri;
            if (offset < totalEdges) {
                return `Triangle edge ${offset}`;
            }
            offset -= totalEdges;
        }
        if (normalsEnabled) {
            return `Triangle normal ${offset}`;
        }
        return `Triangle decoration ${groupId}`;
    };

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
    draw_edges?: boolean;
    edge_radius?: number;
    edge_color?: number;
    show_normals?: boolean;
    normal_length?: number;
    normal_color?: number;
    tag?: string;
    layer_tag?: string;
    structures_coords?: Array<TriangleVerticesInput[] | null>;
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
        console.warn(`[MolSysViewer] Expected ${count} values but got ${value.length}. The first value will be reused.`);
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
            console.warn(`[MolSysViewer] atom_triplets[${i}] is not a valid triplet`);
            continue;
        }

        const locA = lookup.get(triplet[0] as ElementIndex);
        const locB = lookup.get(triplet[1] as ElementIndex);
        const locC = lookup.get(triplet[2] as ElementIndex);
        if (!locA || !locB || !locC) {
            console.warn(`[MolSysViewer] atom_triplets[${i}] does not match atoms in the structure`);
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
            console.warn("[MolSysViewer] add_triangle_faces: atom_triplets provided but no structure loaded");
            return undefined;
        }
        triangles = buildTrianglesFromAtoms(structure, options);
    } else {
        triangles = buildTrianglesFromVertices(options);
    }

    if (triangles.length === 0) {
        console.warn("[MolSysViewer] add_triangle_faces: no valid triangles");
        return undefined;
    }

    const name = triangles.length === 1 ? "Triangle Face" : `${triangles.length} Triangle Faces`;

    const edgesConfig = options.draw_edges
        ? {
            enabled: true,
            radius: Math.max(0.01, options.edge_radius ?? 0.05),
            color: options.edge_color ?? ColorNames.black,
        }
        : undefined;

    const normalsConfig = options.show_normals
        ? {
            enabled: true,
            length: Math.max(0.01, options.normal_length ?? 0.5),
            color: options.normal_color ?? ColorNames.red,
            radius: Math.max(0.005, (options.edge_radius ?? 0.05) * 0.6),
        }
        : undefined;

    return {
        triangles,
        alpha,
        name,
        edges: edgesConfig,
        normals: normalsConfig,
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
// Tetrahedra (tetrahedral meshes)
// ------------------------------------------------------------------

type TetrahedronVertices = [
    [number, number, number],
    [number, number, number],
    [number, number, number],
    [number, number, number],
];

interface TetrahedronSpec {
    vertices: TetrahedronVertices;
    color: number;
    alpha: number;
    label?: string;
}

interface TetrahedraData {
    tetrahedra: TetrahedronSpec[];
    name: string;
    exteriorOnly: boolean;
    edges?: {
        enabled: boolean;
        radius: number;
        color: number;
    };
    normals?: {
        enabled: boolean;
        length: number;
        color: number;
        radius: number;
    };
}

const TetrahedraParams = {
    ...Mesh.Params,
};

type TetrahedraParams = typeof TetrahedraParams;
type TetrahedraProps = PD.Values<TetrahedraParams>;

type FaceVertices = [
    [number, number, number],
    [number, number, number],
    [number, number, number]
];

interface TetraFaceInfo {
    tetraIndex: number;
    vertices: FaceVertices;
}

function faceKey(vertices: FaceVertices) {
    return vertices
        .map(v => v.map(n => Number(n)).join(","))
        .sort()
        .join("|");
}

function collectTetraFaces(data: TetrahedraData): TetraFaceInfo[] {
    const combos: Array<[number, number, number]> = [
        [0, 1, 2],
        [0, 1, 3],
        [0, 2, 3],
        [1, 2, 3],
    ];

    const faceMap = new Map<string, TetraFaceInfo & { count: number }>();

    for (let i = 0; i < data.tetrahedra.length; i++) {
        const tetra = data.tetrahedra[i];
        for (const [a, b, c] of combos) {
            const vertices: FaceVertices = [tetra.vertices[a], tetra.vertices[b], tetra.vertices[c]];
            const key = faceKey(vertices);
            const entry = faceMap.get(key);
            if (entry) {
                entry.count += 1;
            } else {
                faceMap.set(key, { tetraIndex: i, vertices, count: 1 });
            }
        }
    }

    if (!data.exteriorOnly) {
        return Array.from(faceMap.values()).map(({ tetraIndex, vertices }) => ({ tetraIndex, vertices }));
    }

    const exterior: TetraFaceInfo[] = [];
    faceMap.forEach(face => {
        if (face.count === 1) {
            exterior.push({ tetraIndex: face.tetraIndex, vertices: face.vertices });
        }
    });
    return exterior;
}

function buildTetrahedraMesh(data: TetrahedraData, _props: TetrahedraProps, prev?: Mesh): Mesh {
    const state = MeshBuilder.createState(512, 256, prev);
    const faces = collectTetraFaces(data);
    const edgeRadius = data.edges?.radius ?? 0.05;
    const normalLength = data.normals?.length ?? 0.5;
    const normalRadius = data.normals?.radius ?? edgeRadius * 0.6;

    const edgeKeySet = new Set<string>();
    const edges: Array<[[number, number, number], [number, number, number]]> = [];

    // Contar grupos: caras, aristas opcionales, normales opcionales
    const baseDecorGroup = data.tetrahedra.length;
    let decorIndex = 0;

    for (let i = 0, il = faces.length; i < il; i++) {
        const face = faces[i];
        state.currentGroup = face.tetraIndex;
        const [a, b, c] = face.vertices;
        MeshBuilder.addTriangle(
            state,
            Vec3.set(Vec3(), a[0], a[1], a[2]),
            Vec3.set(Vec3(), b[0], b[1], b[2]),
            Vec3.set(Vec3(), c[0], c[1], c[2])
        );

        if (data.edges?.enabled) {
            const faceEdges: Array<[[number, number, number], [number, number, number]]> = [
                [a, b],
                [b, c],
                [c, a],
            ];
            for (const [p1, p2] of faceEdges) {
                const key = `${p1[0]},${p1[1]},${p1[2]}|${p2[0]},${p2[1]},${p2[2]}`;
                const revKey = `${p2[0]},${p2[1]},${p2[2]}|${p1[0]},${p1[1]},${p1[2]}`;
                if (!edgeKeySet.has(key) && !edgeKeySet.has(revKey)) {
                    edgeKeySet.add(key);
                    edges.push([p1, p2]);
                }
            }
        }

        if (data.normals?.enabled) {
            const ab = Vec3();
            const ac = Vec3();
            const normal = Vec3();
            Vec3.set(ab, b[0] - a[0], b[1] - a[1], b[2] - a[2]);
            Vec3.set(ac, c[0] - a[0], c[1] - a[1], c[2] - a[2]);
            Vec3.cross(normal, ab, ac);
            if (Vec3.magnitude(normal) > 1e-6) {
                Vec3.normalize(normal, normal);
                Vec3.scale(normal, normal, normalLength);
                const centroid = Vec3.create(
                    (a[0] + b[0] + c[0]) / 3,
                    (a[1] + b[1] + c[1]) / 3,
                    (a[2] + b[2] + c[2]) / 3
                );
                const tip = Vec3.create(centroid[0] + normal[0], centroid[1] + normal[1], centroid[2] + normal[2]);
                const headStart = Vec3.create(
                    centroid[0] + normal[0] * 0.7,
                    centroid[1] + normal[1] * 0.7,
                    centroid[2] + normal[2] * 0.7
                );
                state.currentGroup = baseDecorGroup + decorIndex++;
                addCylinder(state, centroid, headStart, 1, { radiusTop: normalRadius, radiusBottom: normalRadius, radialSegments: 12 });
                addCylinder(state, headStart, tip, 1, { radiusTop: 0.0001, radiusBottom: normalRadius * 1.8, radialSegments: 12 });
            }
        }
    }

    if (data.edges?.enabled) {
        for (const [p1, p2] of edges) {
            state.currentGroup = baseDecorGroup + decorIndex++;
            addCylinder(
                state,
                Vec3.create(p1[0], p1[1], p1[2]),
                Vec3.create(p2[0], p2[1], p2[2]),
                1,
                { radiusTop: edgeRadius, radiusBottom: edgeRadius, radialSegments: 10 }
            );
        }
    }

    return MeshBuilder.getMesh(state);
}

function applyTetrahedraTransparency(
    repr: Representation<TetrahedraData, TetrahedraParams>,
    data: TetrahedraData
) {
    const loci = repr.getAllLoci().find(Shape.isLoci);
    if (!loci) return;

    const layers = data.tetrahedra
        .map((tetra, idx) => ({ tetra, idx }))
        .filter(({ tetra }) => tetra.alpha < 1)
        .map(({ tetra, idx }) => ({
            loci: ShapeGroup.Loci(loci.shape, [{ ids: OrderedSet.ofSingleton(idx), instance: 0 }]),
            value: 1 - Math.max(0, Math.min(1, tetra.alpha)),
        }));

    const transparency = layers.length > 0 ? Transparency("group-loci", layers) : Transparency.Empty;
    repr.setState({ transparency, alphaFactor: 1 });
}

function getTetrahedraShape(
    _ctx: RuntimeContext,
    data: TetrahedraData,
    _props: TetrahedraProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildTetrahedraMesh(data, _props, shape?.geometry);
    const tetraCount = data.tetrahedra.length;
    const edgesEnabled = !!data.edges?.enabled;
    const normalsEnabled = !!data.normals?.enabled;
    const faces = collectTetraFaces(data);
    const faceCount = faces.length;
    const edgeCount = edgesEnabled ? new Set(faces.flatMap(f => {
        const [a, b, c] = f.vertices;
        return [`${a}|${b}`, `${b}|${c}`, `${c}|${a}`];
    })).size : 0;

    const getColor = (groupId: number) => {
        if (groupId < tetraCount) {
            return Color(data.tetrahedra[groupId].color);
        }
        let offset = groupId - tetraCount;
        if (normalsEnabled) {
            if (offset < faceCount) {
                return Color(data.normals?.color ?? ColorNames.red);
            }
            offset -= faceCount;
        }
        if (edgesEnabled) {
            if (offset < edgeCount) {
                return Color(data.edges?.color ?? ColorNames.black);
            }
        }
        return Color(ColorNames.gray);
    };
    const getSize = () => 1;
    const getLabel = (groupId: number) => {
        if (groupId < tetraCount) {
            return data.tetrahedra[groupId].label ?? `Tetrahedron ${groupId}`;
        }
        let offset = groupId - tetraCount;
        if (normalsEnabled) {
            if (offset < faceCount) {
                return `Tetrahedron normal ${offset}`;
            }
            offset -= faceCount;
        }
        if (edgesEnabled && offset < edgeCount) {
            return `Tetrahedron edge ${offset}`;
        }
        return `Decoration ${groupId}`;
    };

    return Shape.create(data.name, data, mesh, getColor, getSize, getLabel);
}

const TetrahedraVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<TetrahedraData, TetrahedraParams>
    ) => ShapeRepresentation(getTetrahedraShape, Mesh.Utils),
};

type TetrahedraRepresentation = Representation<TetrahedraData, TetrahedraParams>;

function TetrahedraRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<TetrahedraData, TetrahedraParams>
): TetrahedraRepresentation {
    return Representation.createMulti(
        "Tetrahedra",
        ctx,
        getParams,
        Representation.StateBuilder,
        TetrahedraVisuals as unknown as Representation.Def<TetrahedraData, TetrahedraParams>
    );
}

const TetrahedraTransformParams = {
    data: PD.Value<TetrahedraData>(undefined as any),
    props: PD.Value<TetrahedraProps>(undefined as any),
};

type TetrahedraTransformParams = typeof TetrahedraTransformParams;

export const Tetrahedra3D = MSVTransform({
    name: "molsysviewer-tetrahedra-3d",
    display: { name: "Tetrahedra" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: TetrahedraTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Tetrahedra", async ctx => {
            const repr = TetrahedraRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => TetrahedraParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            applyTetrahedraTransparency(repr, params.data);

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Tetrahedra", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            applyTetrahedraTransparency(b.data.repr, newParams.data);
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

type TetraCoordsInput = number[] | [number, number, number];

export interface TetrahedraOptions {
    tetraCoords?: TetraCoordsInput[][][];
    tetra_coords?: TetraCoordsInput[][][];
    atomQuads?: number[][];
    atom_quads?: number[][];
    colors?: number | number[];
    alphas?: number | number[];
    labels?: string | string[];
    exterior_only?: boolean;
    show_all_faces?: boolean;
    draw_edges?: boolean;
    edge_radius?: number;
    edge_color?: number;
    show_normals?: boolean;
    normal_length?: number;
    normal_color?: number;
    tag?: string;
    layer_tag?: string;
    name?: string;
}

function normalizeTetraVertices(entry: TetraCoordsInput[][]): TetrahedronVertices | null {
    if (!Array.isArray(entry) || entry.length !== 4) return null;
    const verts = entry.map(v => {
        if (!Array.isArray(v) || v.length !== 3) return null;
        return [Number(v[0]), Number(v[1]), Number(v[2])] as [number, number, number];
    }) as Array<[number, number, number] | null>;
    if (verts.some(v => v === null)) return null;
    return verts as TetrahedronVertices;
}

function buildTetrahedraFromCoords(options: TetrahedraOptions): TetrahedronSpec[] {
    const coords = options.tetraCoords ?? options.tetra_coords ?? [];
    const normalized = coords
        .map(normalizeTetraVertices)
        .filter((v): v is TetrahedronVertices => v !== null);

    const count = normalized.length;
    if (count === 0) return [];

    const colors = expandToList<number>(options.colors, count, Number, ColorNames.orange);
    const alphas = expandToList<number>(options.alphas, count, v => Math.max(0, Math.min(1, Number(v))), 0.6);
    const labels = expandOptionalToList<string>(options.labels, count, String);

    return normalized.map((verts, idx) => ({
        vertices: verts,
        color: colors[idx],
        alpha: alphas[idx],
        label: labels[idx],
    }));
}

function normalizeQuad(quad: number[]): number[] | null {
    if (!Array.isArray(quad) || quad.length !== 4) return null;
    return quad.map(q => Number(q));
}

function buildTetrahedraFromAtoms(structure: Structure, options: TetrahedraOptions): TetrahedronSpec[] {
    const quads = (options.atomQuads ?? options.atom_quads ?? []).map(normalizeQuad).filter((q): q is number[] => q !== null);
    if (quads.length === 0) return [];

    const lookup = buildUnitLookup(structure);
    const a = Vec3();
    const b = Vec3();
    const c = Vec3();
    const d = Vec3();

    const colors = expandToList<number>(options.colors, quads.length, Number, ColorNames.orange);
    const alphas = expandToList<number>(options.alphas, quads.length, v => Math.max(0, Math.min(1, Number(v))), 0.6);
    const labels = expandOptionalToList<string>(options.labels, quads.length, String);

    const tetrahedra: TetrahedronSpec[] = [];

    for (let i = 0; i < quads.length; i++) {
        const quad = quads[i];
        const locA = lookup.get(quad[0] as ElementIndex);
        const locB = lookup.get(quad[1] as ElementIndex);
        const locC = lookup.get(quad[2] as ElementIndex);
        const locD = lookup.get(quad[3] as ElementIndex);
        if (!locA || !locB || !locC || !locD) {
            console.warn(`[MolSysViewer] atom_quads[${i}] does not match atoms in the structure`);
            continue;
        }

        locA.unit.conformation.position(locA.elementIndex, a);
        locB.unit.conformation.position(locB.elementIndex, b);
        locC.unit.conformation.position(locC.elementIndex, c);
        locD.unit.conformation.position(locD.elementIndex, d);

        tetrahedra.push({
            vertices: [
                [a[0], a[1], a[2]],
                [b[0], b[1], b[2]],
                [c[0], c[1], c[2]],
                [d[0], d[1], d[2]],
            ],
            color: colors[i],
            alpha: alphas[i],
            label: labels[i],
        });
    }

    return tetrahedra;
}

function prepareTetrahedraData(plugin: PluginContext, options: TetrahedraOptions): TetrahedraData | undefined {
    const exteriorOnly = options.exterior_only ?? !options.show_all_faces;
    let tetrahedra: TetrahedronSpec[] = [];

    const atomQuads = options.atomQuads ?? options.atom_quads;
    if (atomQuads && atomQuads.length > 0) {
        const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
        const structure = structureRef?.cell.obj?.data as Structure | undefined;
        if (!structure) {
            console.warn("[MolSysViewer] add_tetrahedra: atom_quads provided but no structure loaded");
            return undefined;
        }
        tetrahedra = buildTetrahedraFromAtoms(structure, options);
    } else {
        tetrahedra = buildTetrahedraFromCoords(options);
    }

    if (tetrahedra.length === 0) {
        console.warn("[MolSysViewer] add_tetrahedra: no valid tetrahedra");
        return undefined;
    }

    const name = options.name ?? (tetrahedra.length === 1 ? "Tetrahedron" : `${tetrahedra.length} Tetrahedra`);

    const edgesConfig = options.draw_edges
        ? {
            enabled: true,
            radius: Math.max(0.01, options.edge_radius ?? 0.05),
            color: options.edge_color ?? ColorNames.black,
        }
        : undefined;

    const normalsConfig = options.show_normals
        ? {
            enabled: true,
            length: Math.max(0.01, options.normal_length ?? 0.5),
            color: options.normal_color ?? ColorNames.red,
            radius: Math.max(0.005, (options.edge_radius ?? 0.05) * 0.6),
        }
        : undefined;

    return {
        tetrahedra,
        name,
        exteriorOnly: !!exteriorOnly,
        edges: edgesConfig,
        normals: normalsConfig,
    };
}

export async function addTetrahedraFromPython(
    plugin: PluginContext,
    options: TetrahedraOptions
): Promise<StateObjectRef<SO.Shape.Representation3D> | undefined> {
    const data = prepareTetrahedraData(plugin, options);
    if (!data) return undefined;

    const props: TetrahedraProps = {
        ...PD.getDefaultValues(TetrahedraParams),
        doubleSided: true,
    };

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        Tetrahedra3D,
        {
            data,
            props,
        } as any,
        { tags: options.tag ?? "molsysviewer:tetrahedra" }
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
    color_by?: "norm" | "component";
    color_mode?: "norm" | "component";
    color_component?: number;
    palette?: number[] | string;
    color_map?: number[] | string;
    radius_scale?: number;
    radial_segments?: number;
    tag?: string;
    layer_tag?: string;
}

function resolveOriginsFromAtoms(
    plugin: PluginContext,
    atomIndices: number[]
): Array<[number, number, number] | undefined> {
    const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
    const structure = structureRef?.cell.obj?.data as Structure | undefined;
    if (!structure) {
        console.warn("[MolSysViewer] add_displacement_vectors: no structure loaded");
        return [];
    }

    const lookup = buildUnitLookup(structure);
    const position = Vec3();
    const origins: Array<[number, number, number] | undefined> = [];

    atomIndices.forEach((idx, pos) => {
        const loc = lookup.get(idx as ElementIndex);
        if (!loc) {
            console.warn(`[MolSysViewer] atom_indices[${pos}] does not match atoms in the structure`);
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
        console.warn("[MolSysViewer] add_displacement_vectors: missing vectors");
        return undefined;
    }

    const origins = options.atom_indices && options.atom_indices.length > 0
        ? resolveOriginsFromAtoms(plugin, options.atom_indices)
        : options.origins ?? [];

    if (!origins || origins.length === 0) {
        console.warn("[MolSysViewer] add_displacement_vectors: no valid origins");
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
    const colorMode: "norm" | "component" = options.color_by ?? options.color_mode ?? "norm";
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
        console.warn("[MolSysViewer] add_displacement_vectors: no usable inputs");
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
        console.warn("[MolSysViewer] add_displacement_vectors: no arrows after filtering");
        return undefined;
    }

    const minValue = Math.min(...colorValues);
    const maxValue = Math.max(...colorValues);
    const domain = minValue === maxValue ? [minValue, minValue + 1] : [minValue, maxValue];
    const paletteInput = options.palette ?? options.color_map;
    const palette = paletteInput && Array.isArray(paletteInput) && paletteInput.length === 0
        ? undefined
        : paletteInput;
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
