import assert from "node:assert";
import { spawn, spawnSync } from "node:child_process";
import { createInterface } from "node:readline";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";

const dir = dirname(fileURLToPath(import.meta.url));

async function checkProgressiveWelcome(page: any, fixture: any) {
    const welcome = page.locator('[data-molsysviewer-welcome-card="true"]');
    const apply = async (messages: unknown[]) => page.evaluate(async items => {
        for (const item of items) await (window as any).__controller.handleMessage(item, { throwOnError: true });
    }, messages);
    await apply([{ op: "clear_all" }]);
    assert.equal(await welcome.count(), 1, "an explicitly empty viewer offers Welcome");
    await apply(fixture.progressive_wire[0]);
    assert.equal(await welcome.count(), 0);
    await page.evaluate(() => {
        const w = window as any;
        w.__welcomeInsertions = 0;
        w.__countWelcome = (records: MutationRecord[]) => {
            for (const record of records) for (const node of record.addedNodes) {
                if (!(node instanceof Element)) continue;
                if (node.matches('[data-molsysviewer-welcome-card="true"]')) w.__welcomeInsertions++;
                w.__welcomeInsertions += node.querySelectorAll('[data-molsysviewer-welcome-card="true"]').length;
            }
        };
        w.__welcomeObserver = new MutationObserver(w.__countWelcome);
        w.__welcomeObserver.observe(document.getElementById("root"), { childList: true, subtree: true });
    });
    for (const messages of fixture.progressive_wire.slice(1)) {
        await apply(messages);
        assert.equal(await welcome.count(), 0);
    }
    const labels = ["Proteína", "Cafeína", "Cafeína__2", "配体"];
    assert.deepEqual(fixture.records.map((record: any) => record.region_tag), labels);
    await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
    await page.locator('[data-molsysviewer-group-panel-tab="regions"]').click();
    const cards = await page.evaluate(() => Array.from(
        document.querySelectorAll('[data-molsysviewer-region-focus]'),
        node => node.textContent,
    ));
    assert.deepEqual(cards.sort(), [...labels].sort(), "Studio renders the original Unicode labels and unique suffix");
    // Use the same tag that is displayed in Studio to act on real Mol* regions.
    const masks = await page.evaluate(async () => {
        const w = window as any, c = w.__controller;
        await c.handleMessage({ op: "hide_region", tag: "Cafeína" }, { throwOnError: true });
        const hidden = w.Harness.inspectSceneTransparency(c, [0, 22, 44, 66]);
        await c.handleMessage({ op: "show_region", tag: "Cafeína" }, { throwOnError: true });
        return { hidden, shown: w.Harness.inspectSceneTransparency(c, [0, 22, 44, 66]) };
    });
    for (const representation of masks.hidden.whole) assert.deepEqual(representation.values, [0, 1, 0, 0]);
    for (const representation of masks.shown.whole) assert.deepEqual(representation.values, [0, 0, 0, 0]);
    assert.ok(masks.hidden.whole.length > 0);
    await apply(fixture.replacement_wire);
    assert.equal(await welcome.count(), 0);
    const insertions = await page.evaluate(() => {
        const w = window as any;
        w.__countWelcome(w.__welcomeObserver.takeRecords());
        w.__welcomeObserver.disconnect();
        return w.__welcomeInsertions;
    });
    assert.equal(insertions, 0, "Welcome must never enter the DOM during progressive loading or replacement");
    // Quick start belongs to an empty, closed canvas; an open Studio stays usable.
    await apply([{ op: "set_panel_mode", expanded: false }]);
    await apply([{ op: "clear_all" }]);
    assert.equal(await welcome.count(), 1);
    const failed = await page.evaluate(async () => {
        const c = (window as any).__controller;
        await c.handleMessage({ op: "clear_all", awaiting_structure: true });
        try {
            await c.handleMessage({ op: "load_structure_from_string", format: "invalid-format", data: "invalid" },
                { throwOnError: true });
            return false;
        } catch { return true; }
    });
    assert.equal(failed, true, "the failure control must actually reject loading");
    assert.equal(await welcome.count(), 1, "a failed prepared load returns to the empty welcome state");
    console.log("[E2E load usability] no transient Welcome; Unicode cards/actions; clear and failed-load controls passed");
}

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
    const options = async (index: number) => {
        const details = page.locator(`[data-molsysviewer-load-options="${index}"]`);
        if (!await details.evaluate((element: HTMLDetailsElement) => element.open)) await details.locator("summary").click();
    };
    let browseCalls = 0;
    const browseReply = async () => {
        const requests = await page.evaluate(() => (window as any).__messages.filter((m: any) => m.action === "browse_load_files"));
        const request = requests[browseCalls++]; assert.ok(request);
        authority.stdin.write(JSON.stringify(request) + "\n");
        const reply = await receive();
        await apply(reply.messages);
        assert.equal(reply.records.length, 0, "browsing and selection must never load molecular data");
    };
    const rendered = async () => page.evaluate(() => {
        const c = (window as any).__controller;
        const structure = c.plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data;
        return { atoms: structure.elementCount, regions: Object.keys((window as any).Harness.inspectScene(c).regions).length };
    });
    const submit = async (navigateWhilePending?: string) => {
        await page.evaluate(() => { (window as any).__loadFormBefore = document.querySelector('[data-molsysviewer-system-load="true"]'); });
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
        if (navigateWhilePending) await page.locator(`[data-molsysviewer-group-panel-tab="${navigateWhilePending}"]`).click();
        authority.stdin.write(JSON.stringify(request) + "\n");
        const result = await receive();
        await apply(result.messages);
        assert.ok(!(await page.locator('[data-molsysviewer-load-submit="true"]').isDisabled()));
        assert.ok(await page.evaluate(() => (window as any).__loadFormBefore === document.querySelector('[data-molsysviewer-system-load="true"]')),
            "structure rebuilds must preserve the loading form and its draft");
        const acknowledgement = result.messages.find((m: any) => m.op === "system_load_result");
        const expectedSection = navigateWhilePending ?? (acknowledgement.ok && acknowledgement.n_atoms > 0 ? "system" : "load");
        assert.equal(await page.locator('[data-molsysviewer-group-panel-tab][aria-current="page"]').getAttribute("data-molsysviewer-group-panel-tab"), expectedSection);
        await page.locator('[data-molsysviewer-group-panel-tab="load"]').click();
        return { request, ...result };
    };
    try {
        const fixture = await receive();
        await page.goto("about:blank");
        await page.setViewportSize({ width: 1200, height: 1000 });
        await page.setContent('<div id="root" style="position:relative;width:1000px;height:850px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { await (window as any).Harness.createController("root", { panelModeStyle: "floating-unified" }); });
        await page.locator('[data-molsysviewer-welcome-load="true"]').click();
        assert.equal(await page.locator('[data-molsysviewer-group-panel-tab]').first().getAttribute("data-molsysviewer-group-panel-tab"), "load");
        assert.equal(await page.locator('[data-molsysviewer-group-panel-tab="load"]').getAttribute("aria-current"), "page");
        assert.equal(await page.locator('[data-molsysviewer-group-panel-section="system"] [data-molsysviewer-system-load]').count(), 0);
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        await page.locator('[data-molsysviewer-system-empty="true"]').getByRole("button", { name: "Load systems", exact: true }).click();
        assert.ok(await row(0, "source").isVisible());
        for (const [width, height] of [[1000, 480], [560, 360], [1000, 850]]) {
            await page.locator("#root").evaluate((element, size) => {
                (element as HTMLElement).style.width = size[0] + "px";
                (element as HTMLElement).style.height = size[1] + "px";
            }, [width, height]);
            await page.waitForFunction(() => {
                const button = document.querySelector<HTMLElement>('[data-molsysviewer-load-submit]')!;
                const rect = button.getBoundingClientRect();
                const host = document.getElementById("root")!.getBoundingClientRect();
                return rect.top >= host.top && rect.bottom <= host.bottom
                    && document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2) === button;
            });
            assert.ok(await row(0, "source").evaluate(element => {
                const rect = element.getBoundingClientRect();
                return document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2) === element;
            }), "source and primary action must be reachable without initial scrolling");
            assert.ok(await page.locator('[data-molsysviewer-load-browse="0"]').evaluate(element => {
                const rect = element.getBoundingClientRect();
                return document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2) === element;
            }), "Browse must be visible next to the source even in a minimum-size canvas");
        }
        assert.equal(await row(0, "label").isVisible(), false, "advanced options start folded");
        assert.equal(await page.locator('[data-molsysviewer-load-operation] option[value="append_structures"]').isDisabled(), true);
        await row(0, "source").press("Enter");
        assert.match(await page.locator('[data-molsysviewer-load-status]').textContent(), /Enter a path/);
        await page.locator("#root").evaluate(element => { (element as HTMLElement).style.height = "480px"; });
        const picker = page.locator('[data-molsysviewer-load-file-picker]');
        await page.locator('[data-molsysviewer-load-browse="0"]').click();
        await page.keyboard.press("Escape");
        await browseReply();
        assert.equal(await picker.isVisible(), false, "a late directory reply cannot reopen a cancelled picker");
        assert.equal(await row(0, "source").inputValue(), "");
        await page.locator('[data-molsysviewer-load-browse="0"]').click(); await browseReply();
        await picker.getByLabel("Python directory", { exact: true }).fill(fixture.directory);
        await picker.getByRole("button", { name: "Open folder", exact: true }).click(); await browseReply();
        await picker.getByLabel("source-0.pdb", { exact: true }).check();
        await picker.getByRole("button", { name: "Next page", exact: true }).click(); await browseReply();
        assert.ok(await picker.getByText("unused-082.txt", { exact: true }).isVisible());
        await picker.getByLabel("Show hidden files", { exact: true }).check(); await browseReply();
        assert.ok(await picker.getByLabel(".hidden-source.pdb", { exact: true }).isVisible());
        await picker.getByLabel("source-1.h5msm", { exact: true }).check();
        await picker.getByRole("button", { name: "Use selected files", exact: true }).click();
        assert.equal(await row(0, "source").inputValue(), fixture.paths[0]);
        assert.equal(await row(1, "source").inputValue(), fixture.paths[1]);
        await page.locator('[data-molsysviewer-load-remove-source="1"]').click();
        await page.locator('[data-molsysviewer-load-browse="0"]').click(); await browseReply();
        await picker.getByLabel("Python directory", { exact: true }).fill(fixture.directory + "/missing");
        await picker.getByRole("button", { name: "Open folder", exact: true }).click(); await browseReply();
        assert.match(await picker.getByRole("status").textContent(), /missing/);
        await picker.getByRole("button", { name: "Cancel", exact: true }).click();
        assert.equal(await row(0, "source").inputValue(), fixture.paths[0], "picker failure/cancellation retains the draft");
        for (let index = 0; index < 4; index++) {
            if (index) await page.locator('[data-molsysviewer-load-add-source="true"]').click();
            await row(index, "source").fill(fixture.paths[index]);
            await options(index);
            await row(index, "label").fill(["A", "A", "C", "D"][index]);
        }
        const batch = await submit("shapes");
        assert.equal(batch.request.multiple, true);
        assert.equal(batch.records.length, 4);
        assert.ok((await page.locator('[data-molsysviewer-load-add-source]').boundingBox())!.height < 48);
        assert.ok((await page.locator('[data-molsysviewer-load-inspect]').boundingBox())!.height < 48,
            "column action buttons must not grow into large empty blocks");
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
        await row(0, "source").fill(fixture.complementary[0]);
        await row(0, "selection").fill("[0,1,2,3,4,5,6,7,8,9]");
        await page.locator('[data-molsysviewer-load-add-source="true"]').click();
        await page.locator('[data-molsysviewer-load-input-mode="true"]').selectOption("complementary");
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
        assert.ok(await page.locator('[data-molsysviewer-load-submit]').isDisabled(),
            "switching an Append draft to independent systems requires an explicit compatible operation");
        assert.match(await page.locator('[data-molsysviewer-load-availability]').textContent(), /one system/);
        await page.locator('[data-molsysviewer-load-operation="true"]').selectOption("replace");
        for (let index = 0; index < 2; index++) {
            await row(index, "source").fill(fixture.trajectory);
            await options(index);
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
        await page.locator('[data-molsysviewer-group-panel-tab="shapes"]').click();
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
            assert.equal(await page.locator('[data-molsysviewer-group-panel-tab="shapes"]').getAttribute("aria-current"), "page",
                "trajectory refreshes preserve explicit Studio navigation");
        }
        await page.setViewportSize({ width: 480, height: 1000 });
        await page.locator("#root").evaluate((el: HTMLElement) => { el.style.width = "420px"; });
        const compact = page.getByRole("combobox", { name: "Studio section", exact: true });
        await compact.waitFor({ state: "visible" });
        assert.equal(await compact.locator("option").first().getAttribute("value"), "load");
        await compact.selectOption("load");
        assert.equal(await row(0, "structures").inputValue(), "2,0");
        await page.goto("about:blank");
        await page.setContent('<div id="root" style="width:1000px;height:850px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { await (window as any).Harness.createController("root", { hasAuthority: false }); });
        assert.equal(await page.locator('[data-molsysviewer-system-load="true"]').count(), 0,
            "an exported browser-only view must not offer Python-backed loading");
        assert.equal(await page.locator('[data-molsysviewer-group-panel-tab="load"]').count(), 0);
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

async function checkRegionEnablement(page: any) {
    const authority = spawn(process.env.PYTHON || "python", [resolve(dir, "composite-load-bridge.py"), "--regions"],
        { cwd: resolve(dir, "../../../.."), stdio: ["pipe", "pipe", "pipe"] });
    const lines = createInterface({ input: authority.stdout })[Symbol.asyncIterator]();
    let stderr = "";
    authority.stderr.on("data", chunk => { stderr += chunk; });
    const receive = async () => {
        let timeout: ReturnType<typeof setTimeout> | undefined;
        try {
            const line = await Promise.race([lines.next(), new Promise<never>((_, reject) => {
                timeout = setTimeout(() => reject(new Error(`Region authority timed out: ${stderr}`)), 60_000);
            })]);
            assert.ok(!line.done, stderr);
            const result = JSON.parse(line.value);
            await page.evaluate(async (messages: unknown[]) => {
                for (const message of messages) await (window as any).__controller.handleMessage(message, { throwOnError: true });
            }, result.messages);
            if (typeof result.enabled === "boolean") {
                await page.waitForFunction(({ enabled, hidden }: { enabled: boolean; hidden: boolean }) => {
                    const card = document.querySelector('[data-molsysviewer-region-card="source"]');
                    return card?.getAttribute("data-molsysviewer-region-enabled") === String(enabled)
                        && card?.getAttribute("data-molsysviewer-region-hidden") === String(hidden);
                }, { enabled: result.enabled, hidden: result.hidden }, { timeout: 10_000 });
            }
            return result;
        } finally { if (timeout) clearTimeout(timeout); }
    };
    const command = async (request: any) => {
        authority.stdin.write(JSON.stringify(request) + "\n");
        return receive();
    };
    const api = (method: string) => command({ review_command: "api", method });
    const inspect = () => page.evaluate(() => {
        const w = window as any;
        return w.Harness.inspectSceneTransparency(w.__controller, [0, 1, 2, 3]);
    });
    const expectWhole = async (expected: number[], hidden = false) => {
        const snapshot = await inspect();
        assert.ok(snapshot.whole.length > 0);
        for (const repr of snapshot.whole) {
            assert.deepEqual(repr.values, expected);
            assert.equal(repr.hidden, hidden);
        }
        assert.ok(snapshot.regions.other.length > 0);
        assert.ok(snapshot.regions.other.every((repr: any) => !repr.hidden));
        assert.ok(snapshot.regions.other.every((repr: any) => repr.values.every((value: number) => value === 0)));
        return snapshot;
    };
    const studio = async (selector: string, action: string) => {
        const before = await page.evaluate(() => (window as any).__messages.length);
        await page.locator(selector).click();
        const requests = await page.evaluate((start: number) => (window as any).__messages.slice(start), before);
        const request = requests.find((item: any) => item.action === action);
        assert.ok(request, `Studio must emit ${action}`);
        assert.equal(request.tag, "source");
        return command(request);
    };
    try {
        await page.goto("about:blank");
        await page.setContent('<div id="root" style="width:1000px;height:850px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => {
            const w = window as any;
            w.__messages = [];
            w.__controller = await w.Harness.createController("root");
        });
        await receive();
        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="regions"]').click();
        const visibility = '[data-molsysviewer-region-buttons-row="source"] [data-molsysviewer-region-visibility="source"]';
        const enabled = '[data-molsysviewer-region-enable="source"]';
        await studio(visibility, "toggle_region_visibility");
        let snapshot = await expectWhole([1, 1, 0, 0]);
        assert.ok(snapshot.regions.source.every((repr: any) => repr.hidden));
        const disabled = await studio(enabled, "toggle_region_enabled");
        assert.equal(disabled.enabled, false);
        assert.equal(disabled.hidden, true);
        snapshot = await expectWhole([0, 0, 0, 0]);
        assert.ok(snapshot.regions.source.every((repr: any) => repr.hidden));
        assert.ok(await page.locator(visibility).isDisabled());
        assert.equal(await page.locator(enabled).isChecked(), false);
        await command({ review_command: "reopen" });
        await expectWhole([0, 0, 0, 0]);
        assert.equal(await page.locator(enabled).isChecked(), false);
        // The fixture forwards region actions; restored Python panel state can
        // legitimately be collapsed. Open Studio before continuing the review.
        await page.evaluate(async () => {
            await (window as any).__controller.handleMessage({ op: "set_panel_mode", panel: "navigate", expanded: true });
        });
        await page.locator('[data-molsysviewer-group-panel-tab="regions"]').click();
        const reenabled = await studio(enabled, "toggle_region_enabled");
        assert.equal(reenabled.enabled, true);
        assert.equal(reenabled.hidden, true);
        await expectWhole([1, 1, 0, 0]);
        await studio(visibility, "toggle_region_visibility");
        snapshot = await expectWhole([1, 1, 0, 0]); // own opaque representation owns these atoms
        assert.ok(snapshot.regions.source.every((repr: any) => !repr.hidden));
        await command({ review_command: "color" });
        const suspendedColors = await api("disable");
        assert.deepEqual(suspendedColors.colors, {});
        const restoredColors = await api("enable");
        assert.deepEqual(restoredColors.colors, { "0": 0xFF0000, "1": 0xFF0000 });
        for (const representation of [null, "inherit", "ball-and-stick"]) {
            await api("hide");
            await command({ review_command: "style", representation });
            await expectWhole([1, 1, 0, 0]);
            await api("disable");
            await expectWhole([0, 0, 0, 0]);
            await api("show"); // a visibility request must not reactivate a disabled region
            await expectWhole([0, 0, 0, 0]);
            await api("hide");
            await api("enable");
            await expectWhole([1, 1, 0, 0]);
        }
        await command({ review_command: "whole", visible: false });
        await api("disable");
        await expectWhole([0, 0, 0, 0], true);
        await api("enable");
        await expectWhole([1, 1, 0, 0], true);
        await command({ review_command: "whole", visible: true });
        await api("show_only");
        await api("disable");
        const afterIsolation = await inspect();
        assert.ok(afterIsolation.whole.every((repr: any) => repr.values[3] === 0), "disabling releases its isolation mask");
        console.log("[E2E regions] real-demo Studio/API hide, suspension, colors, session and independent Whole/regions passed");
    } finally {
        authority.stdin.end();
        authority.kill();
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
        if (process.argv.includes("--regions-only")) {
            await checkRegionEnablement(page);
            assert.deepEqual(errors, []);
            return;
        }
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
        await checkProgressiveWelcome(page, fixture);
        await checkStudioLoading(page);
        await checkRegionEnablement(page);
        assert.deepEqual(errors, []);
        console.log("[E2E composite-load] loading, session reopening, extraction, coordinates and source visibility passed");
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exit(1); });
