// src/shapes.ts

// js/src/shapes.ts

import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { MeshBuilder } from 'molstar/lib/mol-geo/geometry/mesh/mesh-builder';
import { Vec3 } from 'molstar/lib/mol-math/linear-algebra';
import { Color } from 'molstar/lib/mol-util/color';
import { Shape } from 'molstar/lib/mol-model/shape';
import { ShapeRepresentation } from 'molstar/lib/mol-repr/shape/representation';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { ShapeRepresentation3D } from 'molstar/lib/mol-plugin-state/transforms/representation';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { PluginCommands } from 'molstar/lib/mol-plugin/commands';

// 👇 IMPORTANTE: aquí es donde antes usábamos MeshBuilder.addSphere
// ahora usamos la función libre addSphere
import { addSphere } from 'molstar/lib/mol-geo/geometry/mesh/builder/sphere';

export async function addTransparentSphereToPlugin(
    plugin: PluginContext,
    center: [number, number, number],
    radius: number,
    colorHex: number,
    alpha: number,
) {
    // 1. Creamos el mesh de la esfera
    const builder = MeshBuilder.createState(16, 16);
    const pos = Vec3();
    Vec3.set(pos, center[0], center[1], center[2]);

    // detail = 2 es un detalle bastante razonable para test
    addSphere(builder, pos, radius, 2);
    const mesh = MeshBuilder.getMesh(builder);

    // 2. Shape de Mol*
    const color = Color.fromHex(colorHex >>> 0);  // asegurarse de que es unsigned
    const getColor = () => color;
    const getSize = () => 1;
    const getLabel = () => 'transparent-sphere';

    const shape = Shape.create(
        'transparent-sphere',
        {},
        mesh,
        getColor,
        getSize,
        getLabel,
    );

    // 3. Montamos el árbol de estado: Shape -> ShapeRepresentation3D
    const state = plugin.state.data;
    const builderState = state.build();

    const shapeNode = builderState.toRoot().apply(
        StateTransforms.Representation.ShapeRepresentation3D,
        {
            type: 'shape',
            // parámetros de la shape:
            params: {
                alpha,
                ignoreLight: false,
            },
            // pasamos la propia shape
            shape,
        } as any, // según versión de Mol* quizá haga falta this `as any`
        { state: { isGhost: false } },
    );

    await PluginCommands.State.Update(plugin, {
        state,
        tree: builderState,
    });

    // Opcional: centrar cámara en la esfera
    plugin.canvas3d?.requestCameraReset();
}

