import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { PluginStateObject as SO } from "molstar/lib/mol-plugin-state/objects";
import { StateTransformer } from "molstar/lib/mol-state";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";
import { Task } from "molstar/lib/mol-task";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra";
import { Shape } from "molstar/lib/mol-model/shape";
import { ShapeRepresentation } from "molstar/lib/mol-repr/shape/representation";
import { Representation } from "molstar/lib/mol-repr/representation";
import { Text } from "molstar/lib/mol-geo/geometry/text/text";
import { TextBuilder } from "molstar/lib/mol-geo/geometry/text/text-builder";
import { Lines } from "molstar/lib/mol-geo/geometry/lines/lines";
import { LinesBuilder } from "molstar/lib/mol-geo/geometry/lines/lines-builder";
import { Color } from "molstar/lib/mol-util/color";

export interface AnnotationGeometry {
    tag: string;
    text: string;
    anchor: number[];
    position: number[];
    color: number;
    size: number;
    background: boolean;
    backgroundOpacity: number;
    leader: boolean;
    pattern: "solid" | "dashed" | "dotted";
}

const Params = { ...Text.Params, ...Lines.Params };

function textShape(_ctx: any, data: AnnotationGeometry, props: any, previous?: Shape<Text>) {
    const builder = TextBuilder.create(props, 32, 32, previous?.geometry);
    builder.add(data.text, data.position[0], data.position[1], data.position[2], 0, 1, 0);
    return Shape.create(data.tag, data, builder.getText(), () => Color(data.color), () => data.size, () => data.tag);
}

function leaderShape(_ctx: any, data: AnnotationGeometry, _props: any, previous?: Shape<Lines>) {
    const builder = LinesBuilder.create(32, 32, previous?.geometry);
    if (data.leader) {
        const start = Vec3.fromArray(Vec3(), data.anchor, 0);
        const end = Vec3.fromArray(Vec3(), data.position, 0);
        if (data.pattern === "solid") builder.addVec(start, end, 0);
        else {
            // Bounded geometric segments remain part of the canvas and image export.
            const count = data.pattern === "dotted" ? 24 : 12;
            const fraction = data.pattern === "dotted" ? 0.12 : 0.5;
            for (let i = 0; i < count; i++) {
                builder.addVec(Vec3.lerp(Vec3(), start, end, i / count),
                    Vec3.lerp(Vec3(), start, end, (i + fraction) / count), 0);
            }
        }
    }
    return Shape.create(data.tag, data, builder.getLines(), () => Color(data.color), () => 1, () => data.tag);
}

function createRepresentation(plugin: PluginContext) {
    return Representation.createMulti("Annotation", {
        webgl: plugin.canvas3d?.webgl, ...plugin.representation.structure.themes,
    }, () => Params, Representation.StateBuilder, {
        text: () => ShapeRepresentation(textShape, Text.Utils),
        leader: () => ShapeRepresentation(leaderShape, Lines.Utils),
    });
}

function visualProps(data: AnnotationGeometry) {
    return { ...PD.getDefaultValues(Params), offsetX: 0, offsetY: 0, offsetZ: 0,
        tether: false, background: data.background, backgroundOpacity: data.backgroundOpacity };
}

const transform = StateTransformer.builderFactory("molsysviewer")({
    name: "annotation-callout-3d", display: { name: "Annotation" },
    from: SO.Root, to: SO.Shape.Representation3D,
    params: { geometry: PD.Value<AnnotationGeometry>(undefined as any) },
})({
    canAutoUpdate: () => true,
    apply({ params }, plugin: PluginContext) {
        return Task.create("Annotation", async ctx => {
            const repr = createRepresentation(plugin);
            await repr.createOrUpdate(visualProps(params.geometry), params.geometry).runInContext(ctx);
            return new SO.Shape.Representation3D({ repr, sourceData: params.geometry }, { label: params.geometry.text });
        });
    },
    update({ b, newParams }) {
        return Task.create("Annotation", async ctx => {
            await b.data.repr.createOrUpdate(visualProps(newParams.geometry), newParams.geometry).runInContext(ctx);
            b.data.sourceData = newParams.geometry;
            return StateTransformer.UpdateResult.Updated;
        });
    },
    dispose({ b }) { b?.data.repr.destroy(); },
});

export async function renderAnnotation(plugin: PluginContext, geometry: AnnotationGeometry, ref?: string) {
    const tree = plugin.state.data.build();
    let appliedRef = ref;
    if (ref) tree.to(ref).update({ geometry });
    else appliedRef = tree.toRoot().apply(transform, { geometry }, { tags: [geometry.tag, "molsysviewer:annotation"] }).ref;
    await PluginCommands.State.Update(plugin, { state: plugin.state.data, tree, options: { doNotLogTiming: true } });
    return appliedRef!;
}

/** Camera offsets use the camera basis; world anchors never move on camera rotation. */
export function cameraOffsetPosition(anchor: number[], offset: number[], camera: { position: ArrayLike<number>; target: ArrayLike<number>; up: ArrayLike<number> }): number[] {
    const toward = Vec3.normalize(Vec3(), Vec3.sub(Vec3(), camera.position as Vec3, camera.target as Vec3));
    const right = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), camera.up as Vec3, toward));
    const up = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), toward, right));
    return anchor.map((value, i) => value + offset[0] * right[i] + offset[1] * up[i] + offset[2] * toward[i]);
}
