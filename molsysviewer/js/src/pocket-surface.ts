// src/pocket-surface.ts
import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateObjectRef, StateTransformer } from "molstar/lib/mol-state";
import { Task } from "molstar/lib/mol-task";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";
import { Color } from "molstar/lib/mol-util/color";
import { ColorScale } from "molstar/lib/mol-util/color/scale";
import { ColorNames } from "molstar/lib/mol-util/color/names";
import { Vec3, Mat4 } from "molstar/lib/mol-math/linear-algebra";
import { Mesh } from "molstar/lib/mol-geo/geometry/mesh/mesh";
import { Shape } from "molstar/lib/mol-model/shape";
import { ShapeRepresentation } from "molstar/lib/mol-repr/shape/representation";
import {
    Representation,
    RepresentationContext,
    RepresentationParamsGetter,
} from "molstar/lib/mol-repr/representation";
import { GaussianDensityProps, DefaultGaussianDensityProps, computeStructureGaussianDensity } from "molstar/lib/mol-repr/structure/visual/util/gaussian";
import { computeMarchingCubesMesh } from "molstar/lib/mol-geo/util/marching-cubes/algorithm";
import { PhysicalSizeTheme } from "molstar/lib/mol-theme/size/physical";
import { ThemeDataContext } from "molstar/lib/mol-theme/theme";
import { ValueCell } from "molstar/lib/mol-util/value-cell";
import { Structure, StructureElement } from "molstar/lib/mol-model/structure";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { Clip } from "molstar/lib/mol-util/clip";

const MSVTransform = StateTransformer.builderFactory("molsysviewer");

export interface PocketSurfaceOptions {
    atom_indices: number[];
    scalars?: number[];
    grid?: {
        resolution?: number;
        radius_offset?: number;
        smoothness?: number;
    };
    alpha?: number;
    color_map?: number[] | string;
    mouth_atom_indices?: number[][] | number[];
    clip_plane?: {
        point: [number, number, number];
        normal: [number, number, number];
    };
}

type PocketSurfaceData = {
    mesh: Mesh;
    colors: Map<number, Color>;
    alpha: number;
    name: string;
};

const PocketSurfaceParams = {
    ...Mesh.Params,
};
type PocketSurfaceParams = typeof PocketSurfaceParams;
type PocketSurfaceProps = PD.Values<PocketSurfaceParams>;

function getPocketSurfaceName(atomCount: number) {
    return `Pocket Surface (${atomCount} atoms)`;
}

function getColor(colors: Map<number, Color>, defaultColor: Color) {
    return (groupId: number) => colors.get(groupId) ?? defaultColor;
}

function createPocketSurfaceShape(data: PocketSurfaceData, props: PocketSurfaceProps, shape?: Shape<Mesh>) {
    const name = data.name;
    return Shape.create(name, data, data.mesh, getColor(data.colors, Color(ColorNames.grey)), () => 1, () => name, shape?.transforms);
}

const PocketSurfaceVisuals = {
    mesh: (_ctx: RepresentationContext, _getParams: RepresentationParamsGetter<PocketSurfaceData, PocketSurfaceParams>) =>
        ShapeRepresentation(createPocketSurfaceShape, Mesh.Utils),
};

type PocketSurfaceRepresentation = Representation<PocketSurfaceData, PocketSurfaceParams>;

function getDefaultGaussianProps(options?: PocketSurfaceOptions): GaussianDensityProps {
    const defaults = { ...DefaultGaussianDensityProps };
    if (options?.grid?.resolution !== undefined) defaults.resolution = options.grid.resolution;
    if (options?.grid?.radius_offset !== undefined) defaults.radiusOffset = options.grid.radius_offset;
    if (options?.grid?.smoothness !== undefined) defaults.smoothness = options.grid.smoothness;
    return defaults;
}

function normalizeMouths(input?: number[] | number[][]): number[][] {
    if (!input) return [];
    if (Array.isArray(input) && input.length > 0 && Array.isArray(input[0])) {
        return (input as number[][])
            .map(list => list.map(i => Number(i)))
            .filter(list => list.length > 0);
    }
    const flat = Array.isArray(input) ? (input as number[]).map(i => Number(i)) : [];
    return flat.length ? [flat] : [];
}

function createSubsetFromAtomIndices(structure: Structure, atomIndices: number[]): Structure | undefined {
    const wanted = new Set(atomIndices);
    const lociElements: StructureElement.Loci["elements"][0][] = [];

    for (const unit of structure.units) {
        const match: number[] = [];
        const elements = unit.elements;
        const count = OrderedSet.size(elements);
        for (let i = 0; i < count; i++) {
            const element = OrderedSet.getAt(elements, i);
            if (wanted.has(element)) match.push(i);
        }
        if (match.length) {
            lociElements.push({ unit, indices: SortedArray.ofSortedArray(match) as OrderedSet });
        }
    }

    if (lociElements.length === 0) return undefined;
    return StructureElement.toStructure(StructureElement.Loci(structure, lociElements));
}

function buildClipPlanes(structure: Structure, options: PocketSurfaceOptions) {
    const clipObjects: Clip.Params["objects"] = [];

    const mouthList = normalizeMouths(options.mouth_atom_indices);
    if (mouthList.length === 0 && options.clip_plane) {
        clipObjects.push({
            type: "plane",
            invert: false,
            position: Vec3.fromArray(Vec3(), options.clip_plane.point, 0),
            rotation: planeRotationFromNormal(options.clip_plane.normal),
            scale: Vec3.create(1, 1, 1),
            transform: Mat4.identity(),
        });
        return clipObjects;
    }

    const pocketCenter = centroid(structure);
    for (const mouth of mouthList) {
        if (!mouth || mouth.length === 0) continue;
        const mouthStructure = createSubsetFromAtomIndices(structure, mouth);
        if (!mouthStructure) continue;
        const mouthCenter = centroid(mouthStructure);
        const normal = Vec3.normalize(Vec3(), Vec3.sub(Vec3(), mouthCenter, pocketCenter));
        clipObjects.push({
            type: "plane",
            invert: false,
            position: mouthCenter,
            rotation: planeRotationFromNormal(normal),
            scale: Vec3.create(1, 1, 1),
            transform: Mat4.identity(),
        });
    }

    return clipObjects;
}

function planeRotationFromNormal(normalInput: [number, number, number] | Vec3) {
    const normal = Vec3.normalize(Vec3(), normalInput as any);
    const defaultNormal = Vec3.create(0, 0, 1);
    if (Vec3.magnitude(normal) < 1e-5) return { axis: Vec3.create(1, 0, 0), angle: 0 };
    const axis = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), defaultNormal, normal));
    const dot = Vec3.dot(defaultNormal, normal);
    const angle = Math.acos(Math.min(1, Math.max(-1, dot))) * (180 / Math.PI);
    if (Vec3.magnitude(axis) < 1e-5) return { axis: Vec3.create(1, 0, 0), angle: 0 };
    return { axis, angle };
}

function centroid(structure: Structure) {
    const center = Vec3.create(0, 0, 0);
    let count = 0;
    const p = Vec3();
    for (const unit of structure.units) {
        const { elements, conformation } = unit;
        const size = OrderedSet.size(elements);
        for (let i = 0; i < size; i++) {
            conformation.position(OrderedSet.getAt(elements, i), p);
            Vec3.add(center, center, p);
            count += 1;
        }
    }
    if (count > 0) Vec3.scale(center, center, 1 / count);
    return center;
}

function createGaussianSurfaceMesh(structure: Structure, props: GaussianDensityProps, webgl?: any) {
    return Task.create("Pocket Surface Mesh", async ctx => {
        const sizeTheme = PhysicalSizeTheme({ structure } as ThemeDataContext, { scale: 1 });
        const { transform, field, idField, radiusFactor, resolution, maxRadius } =
            await computeStructureGaussianDensity(structure, sizeTheme, props).runInContext(ctx);

        const params = {
            isoLevel: Math.exp(-props.smoothness) / radiusFactor,
            scalarField: field,
            idField,
        };
        const surface = await computeMarchingCubesMesh(params).runAsChild(ctx);
        Mesh.transform(surface, transform);

        if (webgl && !webgl.isWebGL2) {
            Mesh.uniformTriangleGroup(surface);
            ValueCell.updateIfChanged(surface.varyingGroup, false);
        } else {
            ValueCell.updateIfChanged(surface.varyingGroup, true);
        }

        surface.meta.resolution = resolution;
        Mesh.computeNormals(surface);
        surface.setBoundingSphere(structure.boundary.sphere);
        return surface;
    });
}

function buildColorMap(atomIndices: number[], scalars?: number[], colorMap?: number[] | string) {
    const colors = new Map<number, Color>();
    const defaultColor = Color(ColorNames.lightgrey);
    if (!scalars || scalars.length !== atomIndices.length) {
        atomIndices.forEach(id => colors.set(id, defaultColor));
        return colors;
    }

    const min = Math.min(...scalars);
    const max = Math.max(...scalars);
    const domain = min === max ? [min, min + 1] : [min, max];
    const palette = Array.isArray(colorMap) && colorMap.length > 0 ? colorMap : undefined;
    const scale = ColorScale.create({ domain, listOrName: palette ?? "rainbow", minLabel: "min", maxLabel: "max" });

    atomIndices.forEach((id, idx) => {
        colors.set(id, scale.color(scalars[idx]));
    });

    return colors;
}

function createClipProps(structure: Structure, options: PocketSurfaceOptions) {
    const objects = buildClipPlanes(structure, options);
    if (!objects || objects.length === 0) return undefined;
    return {
        variant: "pixel" as Clip.Variant,
        objects,
    };
}

export async function addPocketSurfaceFromPython(plugin: PluginContext, options: PocketSurfaceOptions) {
    const structureRef = plugin.managers.structure.hierarchy.current.structures.slice(-1)[0];
    const structure = structureRef?.cell.obj?.data as Structure | undefined;
    if (!structure) {
        console.warn("[MolSysViewer] add_pocket_surface sin estructura cargada");
        return undefined;
    }

    const subset = createSubsetFromAtomIndices(structure, options.atom_indices);
    if (!subset || subset.elementCount === 0) {
        console.warn("[MolSysViewer] add_pocket_surface sin átomos seleccionados");
        return undefined;
    }

    const gaussianProps = getDefaultGaussianProps(options);
    const mesh = await plugin.runTask(createGaussianSurfaceMesh(subset, gaussianProps, plugin.canvas3d?.webgl));

    const colors = buildColorMap(options.atom_indices, options.scalars, options.color_map);
    const data: PocketSurfaceData = {
        mesh,
        colors,
        alpha: options.alpha ?? 0.4,
        name: getPocketSurfaceName(options.atom_indices.length),
    };

    const clip = createClipProps(subset, options);

    const props: PocketSurfaceProps = {
        ...PD.getDefaultValues(PocketSurfaceParams),
    };
    if (clip) {
        props.clip = clip as any;
    }

    const builder = plugin.state.data.build();
    const node = builder.toRoot().apply(
        PocketSurface3D,
        {
            data,
            props,
        } as any,
        { tags: "molsysviewer:pocketsurface" }
    );

    await PluginCommands.State.Update(plugin, {
        state: plugin.state.data,
        tree: builder,
        options: { doNotLogTiming: true },
    });

    return node.ref;
}

const PocketSurfaceTransformParams = {
    data: PD.Value<PocketSurfaceData>(undefined as any),
    props: PD.Value<PocketSurfaceProps>(undefined as any),
};

type PocketSurfaceTransformParams = typeof PocketSurfaceTransformParams;

export const PocketSurface3D = MSVTransform({
    name: "molsysviewer-pocket-surface-3d",
    display: { name: "Pocket Surface" },
    from: SO.Root,
    to: SO.Shape.Representation3D,
    params: PocketSurfaceTransformParams,
})({
    canAutoUpdate() {
        return true;
    },
    apply({ params }, plugin: PluginContext) {
        return Task.create("Pocket Surface", async ctx => {
            const repr = PocketSurfaceRepresentation(
                { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes },
                () => PocketSurfaceParams
            );

            await repr.createOrUpdate(params.props, params.data).runInContext(ctx);
            repr.setState({ alphaFactor: params.data.alpha });

            return new SO.Shape.Representation3D({ repr, sourceData: params.data }, { label: params.data.name });
        });
    },
    update({ b, newParams }, _plugin: PluginContext) {
        return Task.create("Pocket Surface", async ctx => {
            await b.data.repr.createOrUpdate(newParams.props, newParams.data).runInContext(ctx);
            b.data.repr.setState({ alphaFactor: newParams.data.alpha });
            b.data.sourceData = newParams.data;
            return StateTransformer.UpdateResult.Updated;
        });
    },
});

function PocketSurfaceRepresentation(
    ctx: RepresentationContext,
    getParams: RepresentationParamsGetter<PocketSurfaceData, PocketSurfaceParams>
): PocketSurfaceRepresentation {
    return Representation.createMulti(
        "PocketSurface",
        ctx,
        getParams,
        Representation.StateBuilder,
        PocketSurfaceVisuals as unknown as Representation.Def<PocketSurfaceData, PocketSurfaceParams>
    );
}
