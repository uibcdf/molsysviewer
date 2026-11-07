import assert from "node:assert/strict";
import test from "node:test";
import { BehaviorSubject, Subject } from "rxjs";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { CameraManager } from "molstar/lib/mol-plugin-state/manager/camera";
import { PluginCommandManager } from "molstar/lib/mol-plugin/command";
import { Reset, SetSnapshot } from "molstar/lib/mol-plugin/behavior/static/camera";
import { ButtonsType, ModifiersKeys } from "molstar/lib/mol-util/input/input-observer";
import { MolSysViewerController } from "../../src/managers/viewer-controller";
import { CameraSync, CameraSyncState } from "../../src/managers/camera-sync";
import { SceneHandlers } from "../../src/managers/handlers/scene-handlers";

// These isolate protocol/lifetime scheduling with real Mol* camera state and
// Rx subjects. Molecular rendering and native input are covered in Studio E2E.
function fixture() {
    const camera = new Camera();
    const didDraw = new BehaviorSubject(0), commited = new Subject<number>(), drag = new Subject<any>();
    let request: any, requested = 0, requestedDraws = 0;
    const canvas: any = { camera, didDraw, commited, input: { drag }, controls: { props: {} },
        requestCameraReset(options: any) { request = options; requested++; }, requestDraw() { requestedDraws++; } };
    const controller = Object.create(MolSysViewerController.prototype) as any;
    controller.plugin = { canvas3d: canvas, commands: new PluginCommandManager(), managers: {} };
    controller.plugin.managers.camera = new CameraManager(controller.plugin);
    Reset(controller.plugin);
    SetSnapshot(controller.plugin);
    controller.state = { markIntentionalViewpoint() {} };
    controller.scene = new SceneHandlers(controller.plugin, {} as any, {
        applyCameraNavigation: (operation: any, hooks: any) => controller.withCameraNavigation(operation, hooks),
    } as any);
    controller.syncStripOverlaysForMessage = () => {};
    const state = new CameraSyncState();
    const sync = new CameraSync(controller, { enabled: () => false, interacting: () => false, send() {} }, state);
    const command = (revision: number, snapshot: any) => ({ op: "set_camera_snapshot", camera_revision: revision, snapshot, duration_ms: 0 });
    const apply = async (message: any) => {
        state.receive(message);
        if (!(await sync.handleMessage(message))) await controller.handleMessage(message, { throwOnError: true });
    };
    const commit = (resolved: any) => {
        const pending = request; request = undefined;
        const partial = typeof pending.snapshot === "function" ? pending.snapshot({}, camera) : pending.snapshot;
        camera.setState({ ...resolved, ...partial }, pending.durationMs);
        return partial;
    };
    const draw = () => didDraw.next(didDraw.value + 1);
    return { camera, canvas, controller, state, sync, command, apply, commit, draw, drag, commited,
        requested: () => requested, requestedDraws: () => requestedDraws, pending: () => request };
}

test("camera revision completes only after its correlated resolved reset reaches a real draw", async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        const raw = { up: [0, 2, 0] };
        await f.apply(f.command(1, raw));
        f.camera.setState({ ...f.camera.getSnapshot(), position: [9, 8, 7] } as any, 0);
        f.draw();
        assert.equal(f.sync.completedRevision, 0, "unrelated stateChanged/draw cannot complete the pending provider");
        const resolved = { ...f.camera.getSnapshot(), position: [1, 2, 30], target: [1, 2, 3], radius: 5, radiusMax: 10 };
        assert.equal(f.commit(resolved), raw, "the provider returns the unchanged partial snapshot");
        assert.equal(f.sync.completedRevision, 0);
        f.draw();
        assert.equal(f.sync.completedRevision, 1);
        assert.deepEqual(f.camera.getSnapshot().up, [0, 2, 0]);
    } finally { f.sync.dispose(); }
});

test("old, bare, future and unsafe peer epochs cannot replace a newer camera intent", async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        await f.apply(f.command(2, { position: [1, 2, 30] }));
        const count = f.requested(), snapshot = f.camera.getSnapshot();
        for (const packet of [snapshot, { snapshot, camera_revision: 1 }, { snapshot, camera_revision: 3 },
            { snapshot, camera_revision: -1 }, { snapshot, camera_revision: Number.MAX_SAFE_INTEGER + 1 }]) {
            f.state.receivePeer(packet);
            await f.sync.apply(packet);
        }
        assert.equal(f.requested(), count);
        assert.equal(f.state.revision, 2);
    } finally { f.sync.dispose(); }
});

test("new camera input after receipt supersedes an authority command before it starts", async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        const message = f.command(1, { position: [1, 2, 30] });
        f.state.receive(message);
        f.drag.next({ buttons: ButtonsType.Flag.Primary, modifiers: ModifiersKeys.create(), dx: 2, dy: 1 });
        await f.sync.handleMessage(message);
        assert.equal(f.requested(), 0);
        assert.equal(f.sync.completedRevision, 0);
        f.draw();
        assert.equal(f.sync.completedRevision, 1);
    } finally { f.sync.dispose(); }
});

test("new camera input cancels its owned pending reset without applying the old target", async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        const current = f.camera.getSnapshot();
        await f.apply(f.command(1, { position: [1, 2, 30] }));
        f.drag.next({ buttons: ButtonsType.Flag.Primary, modifiers: ModifiersKeys.create(), dx: 3, dy: 2 });
        assert.deepEqual(f.pending().snapshot, current, "cancellation uses the actual camera, not the superseded target");
        f.commit(current);
        f.draw();
        assert.equal(f.sync.completedRevision, 1);
    } finally { f.sync.dispose(); }
});

test("bootstrap provenance cannot complete a newer authority epoch", async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 4 });
        const data = { cameraSnapshot: f.camera.getSnapshot(), cameraSnapshotRevision: 3 };
        f.state.receiveBootstrap(data);
        await f.sync.applyBootstrap(data);
        f.commit(data.cameraSnapshot);
        f.draw();
        assert.equal(f.state.revision, 4);
        assert.equal(f.sync.completedRevision, 3);
    } finally { f.sync.dispose(); }
});

test("legacy bare camera snapshots remain accepted before a versioned seed", async () => {
    const f = fixture();
    try {
        let received: any;
        f.controller.setCameraSnapshot = async (snapshot: any) => { received = snapshot; };
        const snapshot = { position: [1, 2, 3] };
        await f.sync.apply(snapshot);
        assert.equal(received, snapshot);
    } finally { f.sync.dispose(); }
});

for (const navigation of [
    { op: "reset_view" },
    { op: "reset_camera" },
    { op: "zoom_to_position", center: [5, 6, 7], radius: 2, duration_ms: 75 },
]) test(`later ${navigation.op} replaces an unresolved camera intent and completes its own epoch`, async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        await f.apply(f.command(1, { position: [30, 20, 10] }));
        await f.apply({ ...navigation, camera_revision: 2 });
        const lastRequest = f.pending(), requested = f.requested();
        assert.equal(lastRequest.durationMs, navigation.op === "zoom_to_position" ? 75 : 250,
            "the original Mol* navigation duration remains intact");
        f.draw();
        assert.equal(f.sync.completedRevision, 0, "an unrelated draw cannot complete the replacement");
        const old = { snapshot: f.camera.getSnapshot(), camera_revision: 1 };
        f.state.receivePeer(old);
        await f.sync.apply(old);
        assert.equal(f.requested(), requested, "an older peer cannot revive the discarded pose");
        const focus = f.camera.getFocus([2, 3, 4] as any, 8);
        f.commit({ ...f.camera.getSnapshot(), ...focus, radiusMax: 100 });
        assert.equal(f.sync.completedRevision, 0, "resolving alone does not complete a navigation");
        f.camera.transition.tick(1000);
        const actual = f.camera.getSnapshot();
        assert.deepEqual(actual.target, navigation.op === "zoom_to_position" ? [5, 6, 7] : [2, 3, 4]);
        f.draw();
        assert.equal(f.sync.completedRevision, 2, "the surviving reset's real completed draw resumes relay");
    } finally { f.sync.dispose(); }
});

test("a local reset supersedes a pending pose and completes only its correlated draw", async () => {
    const f = fixture();
    try {
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        await f.apply(f.command(1, { position: [30, 20, 10] }));
        const queuedPeer = { snapshot: f.camera.getSnapshot(), camera_revision: 1 };
        f.state.receivePeer(queuedPeer);
        await f.controller.resetView();
        const requested = f.requested();
        await f.sync.apply(queuedPeer);
        assert.equal(f.requested(), requested, "a peer received before local navigation cannot replay afterward");
        const duringNavigation = { snapshot: f.camera.getSnapshot(), camera_revision: 1 };
        f.state.receivePeer(duringNavigation);
        await f.sync.apply(duringNavigation);
        assert.equal(f.requested(), requested, "a same-epoch peer cannot replace a local navigation awaiting its own draw");
        f.draw();
        assert.equal(f.sync.completedRevision, 0);
        f.commit({ ...f.camera.getSnapshot(), ...f.camera.getFocus([4, 5, 6] as any, 9), radiusMax: 100 });
        f.camera.transition.tick(1000);
        assert.equal(f.sync.completedRevision, 0);
        f.draw();
        assert.equal(f.sync.completedRevision, 1);
        assert.deepEqual(f.camera.getSnapshot().target, [4, 5, 6]);
        const afterNavigation = { snapshot: f.camera.getSnapshot(), camera_revision: 1 };
        f.state.receivePeer(afterNavigation);
        await f.sync.apply(afterNavigation);
        assert.equal(f.requested(), requested + 1, "same-epoch mirroring resumes after the local navigation completes");
    } finally { f.sync.dispose(); }
});

test("a same-pose animated reset requests one actual draw after its transition finishes", async () => {
    const f = fixture();
    try {
        f.camera.setState({ ...f.camera.getSnapshot(), position: [1, 2, 30], target: [1, 2, 3], radius: 5, radiusMax: 10 } as any, 0);
        const pose = f.camera.getSnapshot();
        await f.apply({ op: "set_camera_sync_revision", camera_revision: 0 });
        await f.apply({ ...f.command(1, pose), duration_ms: 250 });
        f.commit(pose);
        assert.equal(f.camera.transition.inTransition, true);
        f.draw();
        assert.equal(f.sync.completedRevision, 0, "a draw during the animation cannot complete the intent");
        f.camera.transition.tick(1000);
        assert.equal(f.camera.transition.inTransition, false);
        assert.deepEqual(f.camera.getSnapshot(), pose);
        const requestedDraws = f.requestedDraws();
        f.commited.next(1000);
        assert.equal(f.requestedDraws(), requestedDraws + 1, "the completed transition must request a real final draw");
        assert.equal(f.sync.completedRevision, 0, "commit notification alone cannot complete the intent");
        f.commited.next(1001);
        assert.equal(f.requestedDraws(), requestedDraws + 1, "only one final draw is requested while it is pending");
        f.draw();
        assert.equal(f.sync.completedRevision, 1);
    } finally { f.sync.dispose(); }
});
