export async function render({ model, el }) {
    el.style.height = "500px";
    el.style.border = "1px solid #ccc";
    el.style.position = "relative";

    // Load Mol* dynamically from CDN
    const molstar = await import("https://unpkg.com/molstar/dist/molstar.esm.js");

    // Create viewer
    const viewer = await molstar.Viewer.create(el, {
        layoutIsExpanded: false,
        layoutShowControls: false,
        viewportShowExpand: false
    });

    // Listen for Python commands
    model.on("msg:custom", async (msg) => {
        if (msg.op === "test_sphere") {
            const MeshBuilder = molstar.MeshBuilder;
            const Vec3 = molstar.Vec3;
            const Shape = molstar.Shape;

            // Build mesh
            const mb = MeshBuilder.createMesh();
            const center = Vec3.create(0,0,0);
            MeshBuilder.addSphere(mb, center, 1.0, 16);

            const mesh = MeshBuilder.getMesh(mb);

            const shape = Shape.create('test-sphere', {}, mesh, () => 0x00ff00);

            await viewer.plugin.builders.shape.addShape(shape);
        }
    });
}
