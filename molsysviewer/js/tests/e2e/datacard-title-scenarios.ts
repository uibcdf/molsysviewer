import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { BrowserContext, Page } from "playwright";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";

/** Observe literal title handling through the real Python/renderer boundary. */
export async function checkDataCardTitles(context: BrowserContext, dir: string): Promise<void> {
    await withFixtureWorkspace("datacard-titles", async workspace => {
        const path = resolve(workspace, "fixture.json");
        const python = spawnSync(process.env.PYTHON || "python", [resolve(dir, "datacard-title-fixture.py"), path], {
            encoding: "utf8", cwd: resolve(dir, "../../../.."), env: fixtureEnvironment(workspace),
            maxBuffer: 16 * 1024 * 1024,
        });
        assert.equal(python.status, 0, python.error?.message || python.stderr || python.stdout);
        const fixture = JSON.parse(await readFile(path, "utf8"));
        const page = await context.newPage();
        const errors: string[] = [];
        let popup: Page | undefined;
        page.on("pageerror", error => errors.push(String(error)));
        try {
            await page.setContent('<!doctype html><html><body><div id="root" style="width:1000px;height:720px"></div></body></html>');
            await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
            await page.evaluate(async load => {
                const controller = await (window as any).Harness.createController("root");
                await controller.handleMessage(load);
            }, fixture.load);
            await page.waitForFunction(expected => (window as any).__controller.getStructureData()?.elementCount === expected,
                fixture.expected.atoms);
            assert.equal(await page.evaluate(() => (window as any).__controller.trajectory.getTrajectoryState().frameCount),
                fixture.expected.structures);
            const show = async (record: any) => page.evaluate(async options => {
                await (window as any).__controller.handleMessage({ op: "set_trajectory_plot", options: { cards: [options] } });
            }, record);
            const card = page.locator('[data-molsysviewer-datacard="literal-card"]');
            const sourceTitle = () => card.locator("[data-molsysviewer-datacard-header]").evaluate(node =>
                node.firstElementChild!.firstElementChild!.textContent);
            const open = async () => {
                const opened = page.waitForEvent("popup");
                await card.getByTitle("Popout card to external window", { exact: true }).click();
                popup = await opened;
                popup.on("pageerror", error => errors.push(String(error)));
                await popup.locator("#card-pop-header").waitFor();
                return popup;
            };
            const check = async (target: Page, expected: string) => {
                assert.equal(await sourceTitle(), expected);
                const header = await target.locator("#card-pop-header").evaluate(node =>
                    ({ text: node.textContent, childElements: node.children.length }));
                assert.deepEqual(header, { text: expected, childElements: 0 });
                assert.equal(await target.title(), expected);
                assert.equal(await target.locator("svg polyline").count(), 1);
            };
            const close = async () => {
                await popup!.close();
                popup = undefined;
                // Closing returns the actual graph asynchronously, not the header icons.
                await card.locator('svg[width="100%"]:has(polyline)').waitFor({ state: "visible" });
            };
            await show(fixture.plots.initial);
            await card.waitFor();
            await check(await open(), fixture.expected.titles.initial);
            await show(fixture.plots.updated);
            await check(popup!, fixture.expected.titles.updated);
            await close();
            await check(await open(), fixture.expected.titles.updated);
            await close();
            await show(fixture.plots.restored);
            await check(await open(), fixture.expected.titles.restored);
            const point = await popup!.locator("svg").evaluate(element => {
                const svg = element as SVGSVGElement;
                const values = svg.querySelector("polyline")!.getAttribute("points")!.trim().split(/\s+/);
                const [x, y] = values[2].split(",").map(Number);
                const point = svg.createSVGPoint();
                point.x = x;
                point.y = y;
                const screen = point.matrixTransform(svg.getScreenCTM()!);
                return { x: screen.x, y: screen.y };
            });
            await popup!.mouse.click(point.x, point.y);
            await page.waitForFunction(() => (window as any).__controller.trajectory.getTrajectoryState().currentFrame === 2);
            assert.deepEqual(errors, []);
            console.log("[E2E DataCard] literal initial/updated/reopened/restored titles and ordinary popup navigation passed");
        } finally {
            if (popup && !popup.isClosed()) await popup.close();
            await page.evaluate(() => (window as any).__controller?.dispose());
            await page.close();
        }
    });
}
