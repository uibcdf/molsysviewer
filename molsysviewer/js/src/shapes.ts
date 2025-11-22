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

import { Mesh } from "molstar/lib/mol-geo/geometry/mesh/mesh";
import { MeshBuilder } from "molstar/lib/mol-geo/geometry/mesh/mesh-builder";
import { addSphere } from "molstar/lib/mol-geo/geometry/mesh/builder/sphere";
import { addCylinder } from "molstar/lib/mol-geo/geometry/mesh/builder/cylinder";

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
// Displacement vectors (arrows)
// ------------------------------------------------------------------

export interface DisplacementVectorSpec {
    origin: [number, number, number];
    displacement: [number, number, number];
}

type DisplacementColorMode = "norm" | "x" | "y" | "z";

type DisplacementVectorEntry = {
    origin: Vec3;
    direction: Vec3;
    length: number;
    value: number;
};

type DisplacementVectorsData = {
    name: string;
    vectors: DisplacementVectorEntry[];
    colors: Color[];
    radius: number;
    headLengthRatio: number;
    headRadiusFactor: number;
};

const DisplacementVectorShapeParamsInternal = {
    ...Mesh.Params,
};
type DisplacementVectorShapeParams = typeof DisplacementVectorShapeParamsInternal;
type DisplacementVectorShapeProps = PD.Values<DisplacementVectorShapeParamsInternal>;

function getDisplacementVectorsName(count: number) {
    if (count === 0) return "Displacement Vectors (empty)";
    if (count === 1) return "Displacement Vector";
    return `${count} Displacement Vectors`;
}

function buildDisplacementColors(values: number[], count: number, colorMap?: number[] | string) {
    const palette = Array.isArray(colorMap) && colorMap.length > 0 ? colorMap : undefined;
    if (values.length === 0) {
        return new Array(count).fill(Color(ColorNames.red));
    }

    const min = Math.min(...values);
    const max = Math.max(...values);
    const domain = min === max ? [min, min + 1] : [min, max];
    const scale = ColorScale.create({ domain, listOrName: palette ?? "rainbow", minLabel: "min", maxLabel: "max" });

    return values.map(v => scale.color(v));
}

const tmpShaftEnd = Vec3();
const tmpArrowEnd = Vec3();

function buildDisplacementVectorMesh(
    data: DisplacementVectorsData,
    _props: DisplacementVectorShapeProps,
    prev?: Mesh
): Mesh {
    const state = MeshBuilder.createState(Math.max(128, data.vectors.length * 8), Math.max(64, data.vectors.length * 2), prev);
    const shaftProps = { radiusTop: data.radius, radiusBottom: data.radius, radialSegments: 32 };
    const headProps = {
        radiusTop: 0,
        radiusBottom: data.radius * data.headRadiusFactor,
        radialSegments: 32,
    };

    for (let i = 0, il = data.vectors.length; i < il; i++) {
        const vector = data.vectors[i];
        if (vector.length <= 0) continue;

        const headLength = Math.min(vector.length, vector.length * data.headLengthRatio);
        const shaftLength = Math.max(0, vector.length - headLength);

        state.currentGroup = i;

        if (shaftLength > 0) {
            Vec3.scaleAndAdd(tmpShaftEnd, vector.origin, vector.direction, shaftLength);
            addCylinder(state, vector.origin, tmpShaftEnd, 1, shaftProps);
        } else {
            Vec3.copy(tmpShaftEnd, vector.origin);
        }

        if (headLength > 0) {
            Vec3.scaleAndAdd(tmpArrowEnd, tmpShaftEnd, vector.direction, headLength);
            addCylinder(state, tmpShaftEnd, tmpArrowEnd, 1, headProps);
        }
    }

    return MeshBuilder.getMesh(state);
}

function getDisplacementVectorShape(
    _ctx: RuntimeContext,
    data: DisplacementVectorsData,
    _props: DisplacementVectorShapeProps,
    shape?: Shape<Mesh>
) {
    const mesh = buildDisplacementVectorMesh(data, _props, shape?.geometry);
    const name = data.name;

    const getColor = (groupId: number) => data.colors[groupId] ?? Color(ColorNames.red);
    const getSize = () => data.radius;
    const getLabel = (groupId: number) => {
        const v = data.vectors[groupId];
        return `Vector ${groupId} (|v| = ${v.length.toFixed(2)})`;
    };

    return Shape.create(name, data, mesh, getColor, getSize, getLabel, shape?.transforms);
}

const DisplacementVectorVisuals = {
    mesh: (
        _ctx: RepresentationContext,
        _getParams: RepresentationParamsGetter<DisplacementVectorsData, DisplacementVectorShapeParamsInternal>
    ) => ShapeRepresentation(getDisplacementVectorShape, Mesh.Utils),
};

export const DisplacementVectorShapeParams = {
    ...DisplacementVectorShapeParamsInternal,
};
export type DisplacementVectorRepresentation = Representation<DisplacementVectorsData, DisplacementVectorShapeParamsInternal>;

function DisplacementVectorRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<DisplacementVectorsData, DisplacementVectorShapeParamsInternal>
): DisplacementVectorRepresentation {
    return Representation.createMulti(
        "DisplacementVectors",
        ctx,
        getParams,
        Representation.StateBuilder,
        DisplacementVectorVisuals as unknown as Representation.Def<
            DisplacementVectorsData,
            DisplacementVectorShapeParamsInternal
        >
    );
}

const DisplacementVectorsParams = {
    vectors: PD.Value<DisplacementVectorSpec[]>([]),
    lengthScale: PD.Numeric(1, { min: 0, max: 1_000_000, step: 0.01 }),
    maxLength: PD.Numeric(0, { min: 0, max: 1_000_000, step: 0.01 }),
    minLength: PD.Numeric(0, { min: 0, max: 1_000_000, step: 0.01 }),
    radius: PD.Numeric(0.2, { min: 0.01, max: 100, step: 0.01 }),
    headLengthRatio: PD.Numeric(0.25, { min: 0.01, max: 0.99, step: 0.01 }),
    headRadiusFactor: PD.Numeric(1.8, { min: 0.1, max: 10, step: 0.1 }),
    colorMode: PD.Select<DisplacementColorMode>("norm", [
        ["norm", "Vector norm"],
        ["x", "X component"],
        ["y", "Y component"],
        ["z", "Z component"],
    ]),
    colorMap: PD.Value<number[] | string>("rainbow" as any),
    alpha: PD.Numeric(1, { min: 0, max: 1, step: 0.01 }),
    name: PD.Text("Displacement Vectors"),
};

type DisplacementVectorsParams = typeof DisplacementVectorsParams;

function sanitizeColorMode(mode?: DisplacementColorMode) {
    if (mode === "x" || mode === "y" || mode === "z") return mode;
    return "norm" as DisplacementColorMode;
}

function selectComponent(vec: Vec3, mode: DisplacementColorMode) {
    if (mode === "x") return vec[0];
    if (mode === "y") return vec[1];
    if (mode === "z") return vec[2];
    return Vec3.magnitude(vec);
}

function createDisplacementVectorsData(params: PD.Values<DisplacementVectorsParams>): DisplacementVectorsData {
    const vectors = params.vectors ?? [];
    const lengthScale = Math.max(0, params.lengthScale ?? 1);
    const minLength = Math.max(0, params.minLength ?? 0);
    const maxLength = Math.max(0, params.maxLength ?? 0);
    const headLengthRatio = Math.min(Math.max(params.headLengthRatio ?? 0.25, 0.01), 0.99);
    const headRadiusFactor = Math.max(params.headRadiusFactor ?? 1.8, 0.1);
    const colorMode = sanitizeColorMode(params.colorMode ?? "norm");

    const entries: DisplacementVectorEntry[] = [];
    const values: number[] = [];

    let maxVectorLength = 0;

    for (const vector of vectors) {
        if (!vector || !vector.origin || !vector.displacement) continue;
        const displacement = Vec3.create(vector.displacement[0], vector.displacement[1], vector.displacement[2]);
        const magnitude = Vec3.magnitude(displacement) * lengthScale;
        if (!Number.isFinite(magnitude) || magnitude <= minLength) continue;

        const direction = Vec3();
        Vec3.normalize(direction, displacement);
        const origin = Vec3.create(vector.origin[0], vector.origin[1], vector.origin[2]);
        const value = selectComponent(displacement, colorMode) * lengthScale;

        entries.push({ origin, direction, length: magnitude, value });
        values.push(colorMode === "norm" ? magnitude : value);
        if (magnitude > maxVectorLength) maxVectorLength = magnitude;
    }

    const normalizationFactor = maxLength > 0 && maxVectorLength > 0 ? maxLength / maxVectorLength : 1;

    for (const entry of entries) {
        entry.length *= normalizationFactor;
    }

    const colorValues = colorMode === "norm" ? values.map(v => v * normalizationFactor) : values;
    const colors = buildDisplacementColors(colorValues, entries.length, params.colorMap);

    return {
        name: (params.name ?? getDisplacementVectorsName(entries.length)) || getDisplacementVectorsName(entries.length),
        vectors: entries,
        colors,
        radius: params.radius ?? 0.2,
        headLengthRatio,
        headRadiusFactor,
    };
}

export const DisplacementVectors3D = MSVTransform({
    name: "molsysviewer-displacement-vectors-3d",
    display: { name: "Displacement Vectors" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: DisplacementVectorsParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Displacement Vectors", async ctx => {
            const data = createDisplacementVectorsData(params);
            const repr = DisplacementVectorRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => DisplacementVectorShapeParams
            );

            const props: DisplacementVectorShapeProps = {
                ...PD.getDefaultValues(DisplacementVectorShapeParams),
            };

            await repr.createOrUpdate(props, data).runInContext(ctx);
            repr.setState({ alphaFactor: params.alpha ?? 1 });

            return new SO.Shape.Representation3D({ repr, sourceData: data }, { label: data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Displacement Vectors", async ctx => {
            const data = createDisplacementVectorsData(newParams);
            const props = { ...b.data.repr.props };
            await b.data.repr.createOrUpdate(props, data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.alpha ?? 1 });
            b.data.sourceData = data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

export interface DisplacementVectorOptions {
    vectors: DisplacementVectorSpec[];
    lengthScale?: number;
    maxLength?: number;
    minLength?: number;
    radius?: number;
    headLengthRatio?: number;
    headRadiusFactor?: number;
    colorMode?: DisplacementColorMode;
    colorMap?: number[] | string;
    alpha?: number;
    name?: string;
    tag?: string;
}

export async function addDisplacementVectorsFromPython(
    plugin: PluginContext,
    options: DisplacementVectorOptions
): Promise<StateObjectRef<SO.Shape.Representation3D>> {
    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        DisplacementVectors3D,
        {
            vectors: options.vectors,
            lengthScale: options.lengthScale ?? 1,
            maxLength: options.maxLength ?? 0,
            minLength: options.minLength ?? 0,
            radius: options.radius ?? 0.2,
            headLengthRatio: options.headLengthRatio ?? 0.25,
            headRadiusFactor: options.headRadiusFactor ?? 1.8,
            colorMode: options.colorMode ?? "norm",
            colorMap: options.colorMap ?? "rainbow",
            alpha: options.alpha ?? 1,
            name: options.name ?? getDisplacementVectorsName(options.vectors.length),
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
