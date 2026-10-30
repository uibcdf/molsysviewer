import assert from "node:assert/strict";
import type { Page } from "playwright";

/** Measure the real shared card, including resize while it remains open. */
export async function checkHelpLayout(page: Page): Promise<void> {
    const root = page.locator("#molsysviewer-root");
    const card = page.locator(".molsysviewer-help-card");
    await page.getByRole("button", { name: "Show canvas controls", exact: true }).focus();
    await page.keyboard.press("Enter");
    await page.locator('button[title="Help (H)"]').click();
    await card.waitFor({ state: "visible" });
    const original = await root.evaluate(el => ({ width: el.style.width, height: el.style.height }));
    const measure = () => card.evaluate(el => {
        const rect = el.getBoundingClientRect(), host = el.parentElement!.getBoundingClientRect();
        return { width: rect.width, height: rect.height, x: rect.x, y: rect.y,
            host: { x: host.x, y: host.y, width: host.width, height: host.height },
            font: parseFloat(getComputedStyle(el).fontSize), overflow: el.scrollWidth > el.clientWidth,
            scrolls: el.scrollHeight > el.clientHeight,
            columns: getComputedStyle(el.querySelector(".molsysviewer-help-grid")!).gridTemplateColumns.split(" ").length };
    });
    await root.evaluate(el => { el.style.width = "420px"; el.style.height = "340px"; });
    await page.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-help-card")!.clientWidth < 400);
    const small = await measure();
    assert.equal(small.columns, 1);
    assert.equal(small.overflow, false, "Small Help must wrap without horizontal overflow");
    assert.equal(small.scrolls, true, "Short canvases retain all rows through scrolling");
    assert.ok(small.x >= small.host.x && small.y >= small.host.y);
    assert.ok(small.x + small.width <= small.host.x + small.host.width + 1);
    assert.ok(small.y + small.height <= small.host.y + small.host.height + 1);
    await root.evaluate(el => { el.style.width = "1600px"; el.style.height = "1000px"; });
    await page.waitForFunction(() => document.querySelector<HTMLElement>(".molsysviewer-help-card")!.clientWidth > 1000);
    const large = await measure();
    assert.ok(large.width > 640, "Large Help must grow past its former fixed cap");
    assert.ok(large.font > small.font, "Large canvases offer larger readable text");
    assert.equal(large.overflow, false);
    assert.equal(large.columns, 2);
    await root.evaluate((el, size) => { el.style.width = size.width; el.style.height = size.height; }, original);
    await page.keyboard.press("Escape");
    await card.waitFor({ state: "hidden" });
    // Editing must keep ordinary and modified H away from canvas shortcuts.
    await root.evaluate(el => {
        const input = document.createElement("input"); input.id = "help-editing-guard"; el.appendChild(input); input.focus();
    });
    await page.keyboard.type("hH");
    assert.equal(await page.locator("#help-editing-guard").inputValue(), "hH");
    assert.equal(await card.isVisible(), false);
    await page.locator("#help-editing-guard").evaluate(el => el.remove());
}
