import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateTransformer } from "molstar/lib/mol-state";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";
import { Task } from "molstar/lib/mol-task";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { Structure, Unit } from "molstar/lib/mol-model/structure";
import { DataLoci, Loci } from "molstar/lib/mol-model/loci";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra";
import { Representation } from "molstar/lib/mol-repr/representation";
import { DistanceParams, DistanceRepresentation } from "molstar/lib/mol-repr/shape/loci/distance";
import { AngleParams, AngleRepresentation } from "molstar/lib/mol-repr/shape/loci/angle";
import { DihedralParams, DihedralRepresentation } from "molstar/lib/mol-repr/shape/loci/dihedral";

interface CentroidMeasurement {
    kind: "distance" | "angle" | "dihedral";
    tag: string;
    endpoints: number[][];
    visualParams: Record<string, unknown>;
}

/** Preserve atom occurrences: repeated indices contribute repeatedly to the mean. */
export function measurementCentroid(structure: Structure | undefined, indices: number[]): Vec3 | undefined {
    if (!structure || indices.length === 0) return undefined;
    const sum = Vec3.zero(), position = Vec3.zero();
    for (const index of indices) {
        const unit = structure.units.find(unit => Unit.isAtomic(unit) && OrderedSet.has(unit.elements, index as any));
        if (!unit) return undefined;
        unit.conformation.position(index as any, position);
        Vec3.add(sum, sum, position);
    }
    return Vec3.scale(sum, sum, 1 / indices.length);
}

function endpointLoci(structure: Structure, indices: number[], tag: string): Loci {
    const center = measurementCentroid(structure, indices);
    if (!center) throw new Error("Measurement endpoint atoms are absent from the structure.");
    return DataLoci("molsysviewer:measurement-centroid", { tag, atom_indices: indices, center }, [0],
        sphere => { Vec3.copy(sphere.center, center); sphere.radius = 0; return sphere; },
        () => indices.length === 1 ? `Atom ${indices[0]}` : `Geometric centroid (${indices.length} atom occurrences)`);
}

function measurementData(structure: Structure, spec: CentroidMeasurement) {
    const loci = spec.endpoints.map(indices => endpointLoci(structure, indices, spec.tag));
    if (spec.kind === "distance") return { pairs: [{ loci: loci as [Loci, Loci] }] };
    if (spec.kind === "angle") return { triples: [{ loci: loci as [Loci, Loci, Loci] }] };
    return { quads: [{ loci: loci as [Loci, Loci, Loci, Loci] }] };
}

function createRepresentation(plugin: PluginContext, kind: CentroidMeasurement["kind"]) {
    const context = { webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes };
    // The representation family changes its data/parameter types, not its lifecycle.
    let repr: Representation<any, any>;
    let params: PD.Params;
    if (kind === "distance") { params = DistanceParams; repr = DistanceRepresentation(context, () => DistanceParams); }
    else if (kind === "angle") { params = AngleParams; repr = AngleRepresentation(context, () => AngleParams); }
    else { params = DihedralParams; repr = DihedralRepresentation(context, () => DihedralParams); }
    return { repr, params };
}

const transform = StateTransformer.builderFactory("molsysviewer")({
    name: "structure-centroid-measurement-3d", display: { name: "Centroid measurement" },
    from: SO.Molecule.Structure, to: SO.Shape.Representation3D,
    params: { measurement: PD.Value<CentroidMeasurement>(undefined as any) },
})({
    canAutoUpdate: () => true,
    apply({ a, params }, plugin: PluginContext) {
        return Task.create("Centroid measurement", async ctx => {
            const spec = params.measurement;
            const { repr, params: visualParams } = createRepresentation(plugin, spec.kind);
            const data = measurementData(a.data, spec);
            await repr.createOrUpdate({ ...PD.getDefaultValues(visualParams), ...spec.visualParams }, data).runInContext(ctx);
            return new SO.Shape.Representation3D({ repr, sourceData: data }, { label: spec.tag });
        });
    },
    update({ a, b, oldParams, newParams }) {
        if (oldParams.measurement.kind !== newParams.measurement.kind) return StateTransformer.UpdateResult.Recreate;
        return Task.create("Centroid measurement", async ctx => {
            const data = measurementData(a.data, newParams.measurement);
            await b.data.repr.createOrUpdate(newParams.measurement.visualParams, data).runInContext(ctx);
            b.data.sourceData = data;
            b.label = newParams.measurement.tag;
            return StateTransformer.UpdateResult.Updated;
        });
    },
    dispose({ b }) { b?.data.repr.destroy(); },
});

/** A structure child follows Mol* trajectory/coordinate updates before their completion. */
export async function renderCentroidMeasurement(plugin: PluginContext, structure: Structure, measurement: CentroidMeasurement) {
    const parent = plugin.helpers.substructureParent.get(structure);
    if (!parent) return undefined;
    const tree = plugin.state.data.build();
    const ref = tree.to(parent.transform.ref).apply(transform, { measurement }, { tags: [measurement.tag] }).ref;
    await PluginCommands.State.Update(plugin, { state: plugin.state.data, tree, options: { doNotLogTiming: true } });
    return ref;
}
