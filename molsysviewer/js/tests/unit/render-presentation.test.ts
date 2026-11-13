import assert from "node:assert/strict";
import test from "node:test";
import { attachRenderPresentation, registerRenderPresentation } from "../../src/plugin/render-presentation";

test("presentation runs before rendering and is attached once per renderer", () => {
    const context: any = {}, camera: any = {}, scene: any = {}, frame = { variant: "color" };
    const order: string[] = [];
    const renderer: any = { update(receivedCamera: unknown, receivedScene: unknown, receivedFrame: unknown) {
        assert.equal(this, renderer);
        assert.equal(receivedCamera, camera); assert.equal(receivedScene, scene);
        assert.equal(receivedFrame, frame); order.push("draw");
    } };
    const release = registerRenderPresentation(context, camera, (current, world) => {
        assert.equal(current, camera); assert.equal(world, scene); order.push("present");
    });
    attachRenderPresentation(renderer, context);
    attachRenderPresentation(renderer, context);
    renderer.update(camera, scene, frame);
    assert.deepEqual(order, ["present", "draw"]);
    release(); renderer.update(camera, scene, frame);
    assert.deepEqual(order, ["present", "draw", "draw"]);
});

test("presentation ownership is isolated by context and releases only its owner", () => {
    const first: any = {}, other: any = {}, camera: any = {}, scene: any = {};
    const calls: string[] = [];
    const one = registerRenderPresentation(first, camera, () => { calls.push("one"); });
    const two = registerRenderPresentation(first, camera, () => { calls.push("two"); });
    const three = registerRenderPresentation(other, camera, () => { calls.push("other"); });
    const renderer: any = { update() { calls.push("draw"); } };
    attachRenderPresentation(renderer, first);
    renderer.update(camera, scene); one(); one(); renderer.update(camera, scene); two(); renderer.update(camera, scene);
    assert.deepEqual(calls, ["one", "two", "draw", "two", "draw", "draw"]);
    three();
});

test("an unexpected presentation failure cannot announce an unprepared draw", () => {
    const context: any = {}, camera: any = {}, scene: any = {}, original = new Error("presentation failed");
    let draws = 0;
    const renderer: any = { update() { draws++; } };
    const release = registerRenderPresentation(context, camera, () => { throw original; });
    attachRenderPresentation(renderer, context);
    assert.throws(() => renderer.update(camera, scene), error => error === original);
    assert.equal(draws, 0); release(); renderer.update(camera, scene); assert.equal(draws, 1);
});
