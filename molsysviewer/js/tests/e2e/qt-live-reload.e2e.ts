import assert from "node:assert";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";
import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function run(): Promise<void> {
    const backend = spawnSync(
        process.env.PYTHON ?? "python",
        [resolve(__dirname, "qt-live-reload-bridge.py")],
        { encoding: "utf8" },
    );
    if (backend.status !== 0) {
        throw new Error(`Qt reload fixture generation failed:\n${backend.stderr || backend.stdout}`);
    }
    const messages = JSON.parse(backend.stdout) as {
        first: Record<string, unknown>;
        second: Record<string, unknown>;
    };

    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        chromiumSandbox: false,
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    } as any);
    try {
        const page = await browser.newPage();
        await page.setContent('<div id="root" style="width:800px;height:600px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as unknown as { Harness?: unknown }).Harness));

        const result = await page.evaluate(async fixture => {
            const browserWindow = window as unknown as {
                Harness: { createController(target: string): Promise<any> };
            };
            const controller = await browserWindow.Harness.createController("root");
            const inspect = () => {
                const structures = controller.plugin.managers.structure.hierarchy.current.structures;
                const last = structures.at(-1);
                return {
                    hierarchyStructures: structures.length,
                    atoms: last?.cell?.obj?.data?.elementCount ?? 0,
                };
            };

            await controller.handleMessage({ op: "clear_all" });
            await controller.handleMessage(fixture.first);
            const first = inspect();

            await controller.handleMessage({ op: "clear_all" });
            await controller.handleMessage(fixture.second);
            const second = inspect();
            return { first, second };
        }, messages);

        assert.deepStrictEqual(
            result.first,
            { hierarchyStructures: 1, atoms: 22 },
            "the first real demo must be the only structure in Mol*",
        );
        assert.deepStrictEqual(
            result.second,
            { hierarchyStructures: 1, atoms: 62 },
            "the second real demo must replace, not coexist with, the first",
        );
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
