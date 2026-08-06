/**
 * Does the Qt delivery shape reopen the S8 ordering hole?
 *
 * S8 exists because a structure can arrive later than the messages that need
 * it, and the handlers that need one return silently instead of failing. On
 * AnyWidget the answer is a Python-side deferral gated on the array-native
 * transfer manager, plus `enqueueMessage`, which chains every message through
 * one promise so handling is serialised.
 *
 * Qt shares neither. It boots the same page an export does (`bootDocsView`),
 * and the bridge delivers each message in its own `runJavaScript` call that
 * fires `Promise.resolve(handler(message)).catch(...)` — it never awaits. And
 * `__molsysviewerDocsHandleMessage` awaits `controller.handleMessage` per
 * invocation, with nothing chaining one invocation to the next.
 *
 * This probe reproduces exactly that: two independent, non-awaited invocations
 * back to back, a structure load followed by a scene op that needs it.
 */
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";
import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function run() {
    const python = spawnSync(
        process.env.PYTHON_BIN || "python",
        [resolve(__dirname, "exported-page-framing-bridge.py")],
        { encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
    );
    if (python.status !== 0) throw new Error(python.stderr || python.stdout);
    const exported = JSON.parse(python.stdout);

    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        chromiumSandbox: false,
        args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"],
    } as any);
    const page = await browser.newPage({ viewport: { width: 900, height: 700 } });

    try {
        await page.goto(pathToFileURL(exported.page).href);
        await page.waitForFunction(() => !!(window as any).__molsysviewerDocsController, { timeout: 60000 });

        const result = await page.evaluate(async () => {
            const controller = (window as any).__molsysviewerDocsController;
            const handler = (window as any).__molsysviewerDocsHandleMessage;
            const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

            // Settle the page's own boot before measuring anything.
            await wait(3000);
            await handler({ op: "clear_all" });
            await wait(500);

            const payload = {
                atoms: {
                    atom_id: [1, 2, 3, 4],
                    element_symbol: ["N", "C", "C", "O"],
                    residue_id: [1, 1, 1, 1],
                    residue_name: ["ALA", "ALA", "ALA", "ALA"],
                    chain_id: ["A", "A", "A", "A"],
                },
                structures: [{ coordinates: [[11.1, 13.2, 8.6], [12.6, 13.3, 8.3], [13.2, 12.0, 8.0], [12.6, 10.9, 8.4]] }],
            };

            // Exactly the Qt bridge's shape: fire and forget, twice, back to back.
            handler({ op: "load_molsys_payload", payload });
            handler({ op: "create_region", tag: "qt-ordering", atom_indices: [0, 1], representation: "ball-and-stick" });
            handler({ op: "add_label", tag: "qt-label", options: { text: "late", atom_indices: [0], tag: "qt-label" } });
            handler({ op: "add_distance_measurement", tag: "qt-distance", options: { tag: "qt-distance", layer_tag: "qt-distance", picks_atom_indices: [[0], [3]], endpoint_kinds: ["atom", "atom"], endpoint_policy: "centroid", endpoint_labels: ["A", "B"], endpoint_atom_indices: [[0], [3]] } });

            await wait(8000);
            const entrelazado = {
                region: controller.hasRegion?.("qt-ordering") ?? null,
                label: controller.annotations?.hasTag?.("qt-label") ?? null,
                measurement: controller.measurements?.hasTag?.("qt-distance") ?? null,
            };

            // CONTROL: las mismas ops, con la estructura ya cargada y esperando.
            await handler({ op: "add_label", tag: "ctl-label",
                options: { text: "control", atom_indices: [0], tag: "ctl-label" } });
            await handler({ op: "add_distance_measurement", tag: "ctl-distance", options: { tag: "ctl-distance", layer_tag: "ctl-distance", picks_atom_indices: [[0], [3]], endpoint_kinds: ["atom", "atom"], endpoint_policy: "centroid", endpoint_labels: ["A", "B"], endpoint_atom_indices: [[0], [3]] } });
            await wait(2000);
            const control = {
                label: controller.annotations?.hasTag?.("ctl-label") ?? null,
                measurement: controller.measurements?.hasTag?.("ctl-distance") ?? null,
            };

            return { entrelazado, control,
                atoms: controller.plugin.managers.structure.hierarchy.current.structures
                    .at(-1)?.cell?.obj?.data?.elementCount ?? 0,
                hasRegion: controller.hasRegion?.("qt-ordering") ?? null,
                hasLabel: controller.annotations?.hasTag?.("qt-label") ?? null,
                hasMeasurement: controller.measurements?.hasTag?.("qt-distance") ?? null,
            };
        });

        console.log("[probe qt-delivery-ordering] atoms=" + result.atoms);
        console.log("[probe qt-delivery-ordering] ENTRELAZADO " + JSON.stringify(result.entrelazado));
        console.log("[probe qt-delivery-ordering] CONTROL     " + JSON.stringify(result.control));
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
