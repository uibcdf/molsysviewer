// Use wall-clock time: Chrome's virtual clock can finish before a GPU draw.
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(new URL("../../molsysviewer/js/package.json", import.meta.url));
const { chromium } = require("playwright");
const [file, executablePath] = process.argv.slice(2);
if (!file || !executablePath) throw new Error("Expected an HTML file and a Chromium executable.");
const browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
try {
    const context = await browser.newContext({ offline: true });
    const page = await context.newPage();
    if (!await page.evaluate(() => document.createElement("canvas").getContext("webgl2") !== null)) {
        throw new Error("WebGL2 is unavailable; exported scene rendering cannot be validated.");
    }
    const errors = [];
    page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
    page.on("pageerror", error => errors.push(String(error)));
    await page.goto(pathToFileURL(file).href);
    await page.waitForFunction(() => {
        const root = document.getElementById("molsysviewer-root");
        return root?.dataset.molsysviewerRendered === "true" || root?.dataset.molsysviewerError === "true";
    }, undefined, { timeout: 45000 });
    const dom = await page.evaluate(() => {
        const clone = document.documentElement.cloneNode(true);
        clone.querySelector("#molsysviewer-runtime-source").textContent = "";
        return clone.outerHTML;
    });
    process.stdout.write(JSON.stringify({ dom, console: errors.join("\n") }));
} finally {
    await browser.close();
}
