import assert from "node:assert";
import { spawn, spawnSync } from "node:child_process";
import { createInterface } from "node:readline";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";

const dir = dirname(fileURLToPath(import.meta.url));

async function checkStudioLoading(page: any) {
    const authority = spawn(process.env.PYTHON || "python", [resolve(dir, "composite-load-bridge.py"), "--studio"],
        { cwd: resolve(dir, "../../../.."), stdio: ["pipe", "pipe", "pipe"] });
    const lines = createInterface({ input: authority.stdout })[Symbol.asyncIterator]();
    let stderr = "";
    authority.stderr.on("data", chunk => { stderr += chunk; });
    const receive = async () => {
        let timeout: ReturnType<typeof setTimeout> | undefined;
        try {
            const line = await Promise.race([lines.next(), new Promise<never>((_, reject) => {
                timeout = setTimeout(() => reject(new Error(`Python Studio response timed out: ${stderr}`)), 60_000);
            })]);
            assert.ok(!line.done, stderr);
            return JSON.parse(line.value);
        } finally { if (timeout) clearTimeout(timeout); }
    };
    const apply = async (messages: unknown[]) => page.evaluate(async (items: unknown[]) => {
        for (const item of items) await (window as any).__controller.handleMessage(item);
    }, messages);
    const row = (index: number, field: string) => page.locator(`[data-molsysviewer-load-source="${index}"] [data-molsysviewer-load-field="${field}"]`);
    const rendered = async () => page.evaluate(() => {
        const c = (window as any).__controller;
        const structure = c.plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data;
        return { atoms: structure.elementCount, regions: Object.keys((window as any).Harness.inspectScene(c).regions).length };
    });
    const submit = async () => {
        const count = await page.evaluate(() => (window as any).__messages.filter((m: any) => m.action === "load_systems").length);
        try {
            await page.locator('[data-molsysviewer-load-submit="true"]').click();
        } catch (error) {
            console.error("Load-button layout", await page.evaluate(() => {
                let element = document.querySelector('[data-molsysviewer-load-submit="true"]') as HTMLElement | null;
                const ancestors: unknown[] = [];
                while (element) {
                    const style = getComputedStyle(element), bounds = element.getBoundingClientRect();
                    ancestors.push({ tag: element.tagName, bounds: bounds.toJSON(), overflow: style.overflow,
                        maxHeight: style.maxHeight, height: style.height, scrollHeight: element.scrollHeight,
                        clientHeight: element.clientHeight, scrollTop: element.scrollTop });
                    element = element.parentElement;
                }
                return ancestors;
            }));
            throw error;
        }
        const requests = await page.evaluate(() => (window as any).__messages.filter((m: any) => m.action === "load_systems"));
        assert.equal(requests.length, count + 1);
        const request = requests[requests.length - 1];
        assert.ok(await page.locator('[data-molsysviewer-load-submit="true"]').isDisabled());
        // An acknowledgment for another endpoint/request must not end this load.
        await apply([{ op: "system_load_result", request_id: "another-request", ok: true }]);
        assert.ok(await page.locator('[data-molsysviewer-load-submit="true"]').isDisabled());
        authority.stdin.write(JSON.stringify(request) + "\n");
        const result = await receive();
        await apply(result.messages);
        assert.ok(!(await page.locator('[data-molsysviewer-load-submit="true"]').isDisabled()));
        return { request, ...result };
    };
    try {
        const fixture = await receive();
        await page.goto("about:blank");
        await page.setViewportSize({ width: 1200, height: 1000 });
        await page.setContent('<div id="root" style="width:1000px;height:850px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { await (window as any).Harness.createController("root"); });
        await page.locator('[data-molsysviewer-welcome-load="true"]').click();
        assert.ok(await row(0, "source").isVisible());
        for (let index = 0; index < 4; index++) {
            if (index) await page.locator('[data-molsysviewer-load-add-source="true"]').click();
            await row(index, "source").fill(fixture.paths[index]);
            await row(index, "label").fill(["A", "A", "C", "D"][index]);
        }
        const batch = await submit();
        assert.equal(batch.request.multiple, true);
        assert.equal(batch.records.length, 4);
        assert.deepEqual(await rendered(), { atoms: 88, regions: 4 });
        assert.match(await page.locator('[data-molsysviewer-load-status="true"]').textContent(), /88 atoms, 1 structures, 4 source/);
        assert.equal(await row(0, "source").inputValue(), fixture.paths[0], "hierarchy refresh must retain the draft");
        for (let index = 3; index > 0; index--) await page.locator(`[data-molsysviewer-load-remove-source="${index}"]`).click();
        await row(0, "source").fill(fixture.paths[0] + ".missing");
        const rejected = await submit();
        assert.equal(rejected.messages.find((m: any) => m.op === "system_load_result").ok, false);
        assert.deepEqual(await rendered(), { atoms: 88, regions: 4 });
        assert.equal(await row(0, "source").inputValue(), fixture.paths[0] + ".missing");
        await row(0, "source").fill(fixture.paths[0]);
        await submit();
        assert.deepEqual(await rendered(), { atoms: 110, regions: 5 });
        await page.locator('[data-molsysviewer-load-operation="true"]').selectOption("replace");
        await submit();
        assert.deepEqual(await rendered(), { atoms: 22, regions: 0 });
        await page.locator('[data-molsysviewer-load-input-mode="true"]').selectOption("complementary");
        await row(0, "source").fill(fixture.complementary[0]);
        await row(0, "selection").fill("[0,1,2,3,4,5,6,7,8,9]");
        await page.locator('[data-molsysviewer-load-add-source="true"]').click();
        await row(1, "source").fill(fixture.complementary[1]);
        assert.equal(await row(1, "selection").count(), 0, "complementary forms share selectors");
        const complementary = await submit();
        assert.equal(complementary.request.multiple, false);
        assert.equal(complementary.records.length, 1);
        assert.deepEqual(await rendered(), { atoms: 10, regions: 0 });
        await page.locator('[data-molsysviewer-load-operation="true"]').selectOption("append_structures");
        const appended = await submit();
        assert.equal(appended.messages.find((m: any) => m.op === "system_load_result").n_structures, 2);
        await page.locator('[data-molsysviewer-load-input-mode="true"]').selectOption("independent");
        await page.locator('[data-molsysviewer-load-operation="true"]').selectOption("replace");
        for (let index = 0; index < 2; index++) {
            await row(index, "source").fill(fixture.trajectory);
            await row(index, "structures").fill(index === 0 ? "2,0" : "1,2");
            await row(index, "selection").fill(index === 0 ? "[0,2]" : "[1,3]");
        }
        const unpaired = await submit();
        assert.equal(unpaired.messages.find((m: any) => m.op === "system_load_result").ok, false);
        assert.deepEqual(await rendered(), { atoms: 10, regions: 0 });
        await page.locator('[data-molsysviewer-load-pairing="true"]').check();
        const paired = await submit();
        assert.deepEqual(paired.request.structure_indices, [[2, 0], [1, 2]]);
        assert.deepEqual(await rendered(), { atoms: 4, regions: 2 });
        for (let frame = 0; frame < 2; frame++) {
            const actual = await page.evaluate(async (index: number) => {
                const c = (window as any).__controller;
                await c.trajectory.setTrajectoryFrame(index);
                const structure = c.plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data;
                const coordinates: number[][] = [];
                for (const unit of structure.units) for (const atom of unit.elements) {
                    const position = [0, 0, 0]; unit.conformation.position(atom, position);
                    coordinates[unit.model.atomicHierarchy.atomSourceIndex.value(atom)] = position;
                }
                return coordinates;
            }, frame);
            actual.forEach((position: number[], atom: number) => position.forEach((value, axis) =>
                assert.ok(Math.abs(value - paired.coordinates[frame][atom][axis]) < 1e-4)));
        }
        await page.goto("about:blank");
        await page.setContent('<div id="root" style="width:1000px;height:850px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { await (window as any).Harness.createController("root", { hasAuthority: false }); });
        assert.equal(await page.locator('[data-molsysviewer-system-load="true"]').count(), 0,
            "an exported browser-only view must not offer Python-backed loading");
        console.log("[E2E Studio loading] empty entry, mixed batch, retry/add/replace, complementary forms, append and trajectory pairing passed");
    } finally {
        if (authority.exitCode === null) {
            let timeout: ReturnType<typeof setTimeout> | undefined;
            const closed = new Promise<void>(resolve => {
                authority.once("exit", () => resolve());
                timeout = setTimeout(() => { authority.kill("SIGTERM"); resolve(); }, 5_000);
            });
            authority.stdin.end();
            await closed;
            if (timeout) clearTimeout(timeout);
        }
    }
}

async function run() {
    const result = spawnSync(process.env.PYTHON || "python", [resolve(dir, "composite-load-bridge.py")],
        { encoding: "utf8", cwd: resolve(dir, "../../../.."), maxBuffer: 16 * 1024 * 1024 });
    assert.equal(result.status, 0, result.stderr);
    const fixture = JSON.parse(result.stdout);
    const browser = await chromium.launch({ headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome" } as any);
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(String(error)));
    try {
        await page.setContent('<div id="root" style="width:800px;height:600px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => {
            (window as any).__controller = await (window as any).Harness.createController("root");
        });
        const apply = async (messages: unknown[]) => page.evaluate(async items => {
            const controller = (window as any).__controller;
            await controller.handleMessage({ op: "clear_all" });
            for (const item of items) await controller.handleMessage(item);
        }, messages);
        const inspect = async () => page.evaluate(() => {
            const w = window as any, controller = w.__controller;
            const structure = controller.plugin.managers.structure.hierarchy.current.structures[0]?.cell.obj.data;
            if (!structure) throw new Error("No rendered composite structure");
            const coordinates: number[][] = [];
            for (const unit of structure.units) {
                const indices = unit.model.atomicHierarchy.atomSourceIndex;
                for (const element of unit.elements) {
                    const position = [0, 0, 0];
                    unit.conformation.position(element, position);
                    coordinates[indices.value(element)] = position;
                }
            }
            return { atoms: structure.elementCount, coordinates,
                scene: w.Harness.inspectScene(controller),
                mask: w.Harness.inspectSceneTransparency(controller, [0, 22, 44, 66]) };
        });
        const checkCoordinates = (actual: number[][]) => {
            assert.equal(actual.length, 88);
            actual.forEach((position, atom) => position.forEach((value, axis) =>
                assert.ok(Math.abs(value - fixture.coordinates[0][atom][axis]) < 1e-4,
                    `Coordinate changed for atom ${atom}, axis ${axis}`)));
        };
        await apply(fixture.batch);
        const batch = await inspect();
        assert.equal(batch.atoms, 88);
        checkCoordinates(batch.coordinates);
        assert.equal(Object.keys(batch.scene.regions).length, 4);
        for (const region of Object.values(batch.scene.regions) as any[]) {
            assert.equal(region.atomCount, 22);
            assert.equal(region.reprs.length, 0);
        }
        for (const [index, messages] of fixture.progressive.entries()) {
            await apply(messages as unknown[]);
            const current = await inspect();
            assert.equal(current.atoms, 22 * (index + 1));
            assert.equal(Object.keys(current.scene.regions).length, index === 0 ? 0 : index + 1);
            if (index === 3) {
                checkCoordinates(current.coordinates);
                assert.deepEqual(current.coordinates, batch.coordinates);
            }
        }
        await apply(fixture.hidden);
        const hidden = await inspect();
        assert.ok(hidden.mask.whole.length > 0);
        for (const representation of hidden.mask.whole) {
            assert.deepEqual(representation.values, [0, 1, 0, 0]);
        }
        await apply(fixture.reopened);
        const reopened = await inspect();
        checkCoordinates(reopened.coordinates);
        assert.deepEqual(reopened.scene, hidden.scene);
        assert.deepEqual(reopened.mask, hidden.mask);
        await apply(fixture.extracted);
        const extracted = await inspect();
        assert.equal(extracted.atoms, 44);
        assert.equal(Object.keys(extracted.scene.regions).length, 2);
        extracted.coordinates.forEach((position, atom) => position.forEach((value, axis) =>
            assert.ok(Math.abs(value - fixture.extracted_coordinates[0][atom][axis]) < 1e-4)));
        assert.ok(extracted.mask.whole.length > 0);
        for (const representation of extracted.mask.whole) {
            assert.deepEqual(representation.values, [1, 0, 0, 0]);
        }
        await checkStudioLoading(page);
        assert.deepEqual(errors, []);
        console.log("[E2E composite-load] loading, session reopening, extraction, coordinates and source visibility passed");
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exit(1); });
