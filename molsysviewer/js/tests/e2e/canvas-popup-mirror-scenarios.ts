import assert from "node:assert/strict";
import { resolve } from "node:path";
import type { Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";

/** Scientific mirror receiving guard, with native GPU picks and a real authority. */
export async function checkCanvasPopupMirror(page: Page, dir: string) {
    const bridge = new PythonFixtureBridge(resolve(dir, "canvas-popup-bridge.py"), resolve(dir, "../../../.."));
    const errors: string[] = [];
    const onError = (error: Error) => errors.push(String(error));
    page.on("pageerror", onError);
    let popup: Page | undefined;
    let releaseFixture: (() => Promise<void>) | undefined;
    try {
        releaseFixture = await mountCanvasPopupFixture(page, bridge);
        await captureCanvasPopupControllers(page);
        const opened = page.waitForEvent("popup");
        await page.getByTitle("Open popup", { exact: true }).click();
        popup = await opened;
        popup.on("pageerror", onError);
        await popup.waitForFunction(() => !!(window as any).__mirrorController);
        await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
        const peer = popup;
        const cameraEqual = async () => {
            await peer.bringToFront();
            await peer.waitForFunction(() => {
                const a = (window.opener as any).__mirrorController.getCameraSnapshot();
                const b = (window as any).__mirrorController.getCameraSnapshot();
                return ["position", "target", "up"].every(key => a[key].every((v: number, i: number) => Math.abs(v - b[key][i]) < 1e-5));
            });
        };
        const frameEqual = async () => peer.waitForFunction(() => {
            const a = (window.opener as any).__mirrorController.trajectory.getTrajectoryState();
            const b = (window as any).__mirrorController.trajectory.getTrajectoryState();
            return a.currentFrame === b.currentFrame;
        });
        const fixture = async (action: string, details = {}) => {
            await page.evaluate(message => (window as any).__popupWidgetModel.send(message), { mirror_fixture: action, ...details });
            await page.evaluate(() => (window as any).__popupFixtureDrain());
            assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
        };
        const menu = async (canvas: Page, label: string, view = false) => {
            await canvas.bringToFront();
            const bounds = await canvas.locator("canvas").boundingBox(); assert.ok(bounds);
            await canvas.mouse.click(bounds.x + 20, bounds.y + bounds.height - 30, { button: "right" });
            const context = canvas.locator('[data-molsysviewer-context-menu="true"]');
            await context.waitFor({ state: "visible" });
            if (view) await context.locator('[data-molsysviewer-context-submenu="View"]').click();
            await context.getByRole("menuitem", { name: label, exact: true }).first().click();
        };
        await cameraEqual();
        await fixture("seed");
        for (const canvas of [page, peer]) await canvas.waitForFunction(() => {
            const c = (window as any).__mirrorController;
            return c.interactionSummaries.some((x: any) => x.tag === "mirror-hbonds" && x.n_observations > 0)
                && c.shapeSummaries.some((x: any) => x.tag === "mirror-sphere");
        });

        // Different atom subsets within the same group must converge, including
        // public Python changes after native/user-driven selections.
        for (const [canvas, indices] of [[peer, [0, 1, 2]], [page, [4, 5]]] as [Page, number[]][]) {
            await canvas.evaluate(indices => {
                const c = (window as any).__mirrorController;
                c.activeSelection.setFromAtomIndices(indices, c.getStructureData());
            }, indices);
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(indices =>
                JSON.stringify((window as any).__mirrorController.currentActiveSelection.atom_indices) === JSON.stringify(indices), indices);
        }
        await fixture("selection", { indices: [0, 1] });
        for (const canvas of [page, peer]) await canvas.waitForFunction(() =>
            JSON.stringify((window as any).__mirrorController.currentActiveSelection.atom_indices) === "[0,1]");

        // Camera focus/reset and pointer/wheel updates must include their final
        // applied viewpoint, rather than stopping at pointerup.
        for (const canvas of [page, peer]) {
            await canvas.bringToFront();
            const beforeDrag = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().position);
            const bounds = await canvas.locator("canvas").boundingBox(); assert.ok(bounds);
            await canvas.mouse.move(bounds.x + bounds.width * .55, bounds.y + bounds.height * .6);
            await canvas.mouse.down();
            await canvas.mouse.move(bounds.x + bounds.width * .7, bounds.y + bounds.height * .65, { steps: 14 });
            await canvas.mouse.up();
            await canvas.waitForFunction(before => (window as any).__mirrorController.getCameraSnapshot().position
                .some((v: number, i: number) => Math.abs(v - before[i]) > 1e-4), beforeDrag);
            await cameraEqual();
            await canvas.bringToFront();
            await canvas.mouse.move(bounds.x + bounds.width * .6, bounds.y + bounds.height * .6);
            const beforeWheel = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().position);
            await canvas.mouse.wheel(0, 180);
            await canvas.waitForFunction(before => (window as any).__mirrorController.getCameraSnapshot().position
                .some((v: number, i: number) => Math.abs(v - before[i]) > 1e-4), beforeWheel);
            await cameraEqual();
            for (const action of ["Focus All", "Reset View"]) {
                const before = await canvas.evaluate(() => (window as any).__mirrorController.getCameraSnapshot().position);
                await menu(canvas, action);
                await canvas.waitForFunction(before => {
                    const c = (window as any).__mirrorController;
                    return !c.plugin.canvas3d.camera.transition.inTransition && c.getCameraSnapshot().position
                        .some((v: number, i: number) => Math.abs(v - before[i]) > 1e-4);
                }, before);
                await cameraEqual();
            }
        }
        for (const [canvas, start, stop, flag] of [
            [peer, "Start Automatic Rotation", "Stop Automatic Rotation", "isSpinActive"],
            [page, "Start Swing", "Stop Swing", "isSwingActive"],
        ] as [Page, string, string, string][]) {
            await menu(canvas, start, true);
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(flag => (window as any).__mirrorController[flag], flag);
            assert.equal(await peer.evaluate(() => (window as any).__mirrorController.plugin.canvas3d.props.trackball.animate.name), "off");
            await menu(canvas, stop, true);
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(flag => !(window as any).__mirrorController[flag], flag);
            await cameraEqual();
        }

        // Isolate a visible shape and label for real GPU picking. The snapshot
        // comes through Python and is shared; no synthetic loci are supplied.
        const snapshot = await page.evaluate(() => (window as any).__mirrorController.getCameraSnapshot());
        await fixture("camera", { snapshot: { ...snapshot, position: [0, 0, 120], target: [0, 0, 0], up: [0, 1, 0], radius: 50, radiusMax: 100 } });
        await cameraEqual();
        for (const canvas of [page, peer]) await canvas.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        const nativePick = async (canvas: Page, kind: string, tag: string, position: number[]) => {
            await canvas.bringToFront();
            // Updating a label commits a new representation before the next
            // render invalidates the old GPU pick image. Wait for the actual
            // new hit, not just the Python/Studio text summary.
            const picked = await canvas.waitForFunction(({ kind, tag, position }) => {
                const c = (window as any).__mirrorController;
                const center = (window as any).Harness.projectScenePosition(c, position);
                const rect = c.plugin.canvas3dContext.canvas.getBoundingClientRect();
                const gpu = c.plugin.canvas3d;
                for (const dx of [0, 4, 8, 12, 20, 30, -4, -8]) for (const dy of [0, 3, -3, 6, -6]) {
                    const x = center.x + dx, y = center.y + dy;
                    const hit = gpu.identify([x - rect.left, y - rect.top]);
                    if (!hit) continue;
                    const loci = gpu.getLoci(hit.id).loci;
                    const owner = loci?.shape ? c.state.findShapeOwner(loci.shape.sourceData) : null;
                    if (owner?.kind === kind && owner?.tag === tag) return { x, y };
                }
                return false;
            }, { kind, tag, position });
            const point = await picked.jsonValue() as { x: number; y: number };
            const diagnostic = point ? null : await canvas.evaluate(({ kind, tag }) => {
                const c = (window as any).__mirrorController;
                return (window as any).Harness.inspectTaggedRefs(c, kind, tag).map((entry: any) => {
                    const data = c.plugin.state.data.cells.get(entry.ref)?.obj?.data;
                    return { source: data?.sourceData, loci: data?.repr?.getAllLoci?.().map((l: any) => ({
                        kind: l.kind, name: l.shape?.name, groupCount: l.shape?.groupCount,
                        owner: c.state.findShapeOwner(l.shape?.sourceData),
                    })), objects: data?.repr?.renderObjects.map((ro: any) => ({ type: ro.type, state: ro.state })) };
                });
            }, { kind, tag });
            assert.ok(point, `native GPU pick must find ${kind}:${tag}; ${JSON.stringify(diagnostic)}`);
            await canvas.mouse.click(point.x, point.y);
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(({ kind, tag }) => {
                const c = (window as any).__mirrorController;
                const item = c.activeSelection.getCurrentItems().find((x: any) => x.source_kind === kind && x.tag === tag);
                if (!item) return false;
                const loci = item._loci;
                if (!loci?.shape) return false;
                const refs = (window as any).Harness.inspectTaggedRefs(c, kind, tag);
                return refs.some((entry: any) => c.plugin.state.data.cells.get(entry.ref)?.obj?.data?.repr?.renderObjects
                    .some((ro: any) => ro.values.tMarker?.ref.value.array.some((value: number) => (value & 2) !== 0)));
            }, { kind, tag }).catch(async error => {
                const state = await endpoint.evaluate(({ kind, tag }) => {
                    const c = (window as any).__mirrorController;
                    return { items: c.activeSelection.getCurrentItems().map((item: any) => ({
                        ...item, lociKind: item._loci?.kind, shapeId: item._loci?.shape?.id,
                    })), refs: (window as any).Harness.inspectTaggedRefs(c, kind, tag).map((entry: any) => {
                        const repr = c.plugin.state.data.cells.get(entry.ref)?.obj?.data?.repr;
                        return { ...entry, shapeIds: repr?.getAllLoci?.().map((l: any) => l.shape?.id),
                            markers: repr?.renderObjects.map((ro: any) => Array.from(ro.values.tMarker?.ref.value.array ?? [])) };
                    }) };
                }, { kind, tag });
                throw new Error(`Native selection ${kind}:${tag} did not mark ${endpoint === page ? "original" : "popup"}: ${JSON.stringify(state)}`, { cause: error });
            });
        };
        await nativePick(peer, "shape", "mirror-sphere", [30, 30, 30]);
        await nativePick(page, "annotation", "mirror-label", [0, 30, 0]);
        await fixture("update-label");
        for (const endpoint of [page, peer]) await endpoint.waitForFunction(() =>
            (window as any).__mirrorController.annotationSummaries.find((x: any) => x.tag === "mirror-label")?.text === "Mirror revised");
        await nativePick(peer, "annotation", "mirror-label", [0, 30, 0]);
        for (const endpoint of [page, peer]) assert.equal(await endpoint.evaluate(() => {
            const c = (window as any).__mirrorController;
            const refs = (window as any).Harness.inspectTaggedRefs(c, "annotation", "mirror-label");
            return refs.length === 1 && refs.every((entry: any) => c.plugin.state.data.tree.transforms.has(entry.ref));
        }), true, "label replacement retains only its live representation reference");
        for (const canvas of [page, peer]) assert.equal(await canvas.evaluate(() => {
            const c = (window as any).__mirrorController;
            const shape = c.state.resolveObjectLoci("interaction", "mirror-hbonds")?.shape;
            const data = shape.sourceData.interaction;
            const identity = { kind: "interaction", analysis_name: data.analysis_name,
                analysis_revision: data.analysis_revision, query_revision: data.query_revision,
                frame: data.frame, occurrence_index: data.observations[0].occurrence_index };
            const groups = [{ ids: [0], instance: 0 }];
            return !!c.state.resolveObjectLoci("interaction", "mirror-hbonds", groups, identity)
                && !c.state.resolveObjectLoci("interaction", "mirror-hbonds", groups, { ...identity, frame: identity.frame + 1 });
        }), true, "an old occurrence must not select a reused graphical group on another frame");

        // Dock/ambient are window-local in both directions. Shared preferences
        // continue to use the existing trait projection guard.
        for (const canvas of [peer, page]) {
            await canvas.bringToFront();
            await canvas.getByRole("button", { name: "Panel", exact: true }).click();
            await canvas.getByTitle("Dock panel (Split)", { exact: true }).click();
            assert.equal(await canvas.evaluate(() => (window as any).__mirrorController.sharedShell.isSplit), true);
            const other = canvas === peer ? page : peer;
            assert.equal(await other.evaluate(() => (window as any).__mirrorController.sharedShell.isSplit), false);
            await canvas.getByTitle("Float panel", { exact: true }).click();
            await canvas.locator("canvas").focus(); await canvas.keyboard.press("Escape");
        }
        await fixture("hide");
        for (const canvas of [page, peer]) await canvas.waitForFunction(() => {
            const c = (window as any).__mirrorController;
            return c.shapeSummaries.find((x: any) => x.tag === "mirror-sphere")?.hidden
                && c.annotationSummaries.find((x: any) => x.tag === "mirror-label")?.hidden;
        });
        await fixture("show");
        await fixture("fps", { fps: 8 });
        for (const endpoint of [page, peer]) await endpoint.waitForFunction(() =>
            (document.querySelector('input[title="FPS"]') as HTMLInputElement)?.value === "8");

        // With derived geometry in flight, stop must leave both actual frames
        // and each set's frame-specific geometry at the authority's final frame.
        for (const canvas of [peer, page]) {
            await canvas.bringToFront();
            await canvas.locator('[data-molsysviewer-trajectory-playback="play"]').click();
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(() => (window as any).__mirrorController.trajectory.getTrajectoryState().isPlaying);
            await fixture("fps", { fps: 12 });
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(() =>
                (window as any).__mirrorController.trajectory.getTrajectoryState().isPlaying
                && (document.querySelector('input[title="FPS"]') as HTMLInputElement)?.value === "12");
            await canvas.locator('[data-molsysviewer-trajectory-playback="play"]').click();
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(() => !(window as any).__mirrorController.trajectory.getTrajectoryState().isPlaying);
            await page.evaluate(() => (window as any).__popupFixtureDrain());
            await frameEqual();
            for (const endpoint of [page, peer]) await endpoint.waitForFunction(() => {
                const c = (window as any).__mirrorController;
                const frame = c.trajectory.getTrajectoryState().currentFrame;
                return c.interactionSummaries.find((x: any) => x.tag === "mirror-hbonds")?.frame === frame;
            });
            const stoppedFrame = await page.evaluate(() => (window as any).__mirrorController.trajectory.getTrajectoryState().currentFrame);
            await peer.evaluate(async () => { for (let i = 0; i < 12; i++) await new Promise(requestAnimationFrame); });
            await frameEqual();
            assert.equal(await peer.evaluate(() => (window as any).__mirrorController.trajectory.getTrajectoryState().currentFrame), stoppedFrame);
        }
        await cameraEqual();
        assert.deepEqual(errors, []);
        assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
        console.log("[E2E popup mirror] bidirectional focus/reset/drag/wheel, single motion/playback clocks, exact atom subsets, native shape/annotation picks and markers, local Dock, scene objects and frame-specific hbonds converge");
    } finally {
        page.off("pageerror", onError);
        await page.evaluate(async () => { (window as any).__popupWidgetDispose?.(); await (window as any).__popupFixtureDrain?.(); });
        await bridge.close();
        await releaseFixture?.();
        if (popup && !popup.isClosed()) await popup.close();
    }
}
