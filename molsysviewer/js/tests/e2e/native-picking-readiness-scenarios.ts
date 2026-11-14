import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { DefaultPluginSpec } from 'molstar/lib/mol-plugin/spec';
import { Shape } from 'molstar/lib/mol-model/shape';
import { ShapeRepresentation } from 'molstar/lib/mol-repr/shape/representation';
import { Mesh } from 'molstar/lib/mol-geo/geometry/mesh/mesh';
import { MeshBuilder } from 'molstar/lib/mol-geo/geometry/mesh/mesh-builder';
import { addSphere } from 'molstar/lib/mol-geo/geometry/mesh/builder/sphere';
import { Vec2, Vec3 } from 'molstar/lib/mol-math/linear-algebra';
import { Color } from 'molstar/lib/mol-util/color';

async function createSurface() {
    const host = document.createElement('div');
    Object.assign(host.style, { position: 'relative', width: '480px', height: '360px' });
    const canvas = document.createElement('canvas');
    Object.assign(canvas.style, { width: '100%', height: '100%', display: 'block' });
    host.append(canvas); document.body.append(host);
    const plugin = new PluginContext(DefaultPluginSpec());
    let representation: ReturnType<typeof ShapeRepresentation> | undefined;
    let closed = false;
    const dispose = () => {
        if (closed) return;
        closed = true;
        try { if (representation) { plugin.canvas3d?.remove(representation); representation.destroy(); } }
        finally { plugin.dispose(); host.remove(); }
    };
    try {
        await plugin.init();
        if (!await plugin.initViewerAsync(canvas, host)) throw new Error('Native WebGL initialization failed.');
        // Retain manual drawing while preventing unrelated animation ticks.
        plugin.animationLoop.stop();
        const c = plugin.canvas3d!;
        if (typeof (c.webgl.gl as WebGL2RenderingContext).fenceSync !== 'function') {
            throw new Error('This native GPU control requires WebGL2.');
        }
        const builder = MeshBuilder.createState(128, 64);
        builder.currentGroup = 0;
        addSphere(builder, Vec3.create(0, 0, 0), 3, 2);
        const mesh = MeshBuilder.getMesh(builder);
        representation = ShapeRepresentation((_ctx, data: Mesh) => Shape.create('native-sphere', data, data,
            () => Color(0x008800), () => 1, () => 'native-sphere'), Mesh.Utils);
        await representation.createOrUpdate({ alpha: 1 }, mesh).run();
        c.add(representation);
        c.requestCameraReset({ durationMs: 0 });
        c.requestDraw(); c.tick(performance.now(), { isSynchronous: true });
        return { c, point: Vec2.create(canvas.clientWidth / 2, canvas.clientHeight / 2), dispose };
    } catch (error) { dispose(); throw error; }
}

async function observe(surface: Awaited<ReturnType<typeof createSurface>>) {
    const { c, point } = surface;
    const camera = JSON.stringify(c.camera.getSnapshot());
    const before = c.identify(point);
    if (!before || (c.getLoci(before.id).loci as any).shape?.name !== 'native-sphere') {
        throw new Error('Positive control: native synchronous picking must identify the visible sphere.');
    }
    c.requestDraw(); c.tick(performance.now(), { isSynchronous: true });
    const pending = c.asyncIdentify(point);
    // Same JavaScript task: no sleep, input injection or pending read first.
    const during = c.identify(point);
    let resolved: ReturnType<NonNullable<typeof pending>['tryGet']> = 'pending';
    const deadline = performance.now() + 5000;
    while (resolved === 'pending' && performance.now() < deadline) {
        resolved = pending?.tryGet();
        if (resolved === 'pending') await new Promise<void>(r => requestAnimationFrame(() => r()));
    }
    const after = c.identify(point);
    if (!after || (c.getLoci(after.id).loci as any).shape?.name !== 'native-sphere') {
        throw new Error('Positive control: picking after async completion must still identify the sphere.');
    }
    return { before: before.id, during: during?.id ?? null,
        resolved: resolved && resolved !== 'pending' ? resolved.id : null, after: after.id,
        cameraUnchanged: camera === JSON.stringify(c.camera.getSnapshot()),
        cameraTransition: c.camera.transition.inTransition };
}

/** Same real-native GPU experiment for an original or explicitly repaired build. */
export async function probeNativePickingReadiness() {
    let first: Awaited<ReturnType<typeof createSurface>> | undefined;
    let second: Awaited<ReturnType<typeof createSurface>> | undefined;
    try {
        first = await createSurface();
        const primary = await observe(first);
        const witnessCamera = JSON.stringify(first.c.camera.getSnapshot());
        second = await createSurface();
        const peer = await observe(second);
        second.dispose(); second = undefined;
        const witness = first.c.identify(first.point);
        return { primary, peer, witness: witness?.id ?? null,
            witnessCameraUnchanged: witnessCamera === JSON.stringify(first.c.camera.getSnapshot()) };
    } finally { second?.dispose(); first?.dispose(); }
}
