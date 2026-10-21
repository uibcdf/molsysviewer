import assert from "node:assert/strict";
import type { Page } from "playwright";

/** Real shell geometry and the accepted opacity cycle; rendering is not replaced. */
export async function checkStudioCardDefaults(page: Page) {
    const state = () => page.evaluate(() => {
        const shell = (window as any).__controller.sharedShell;
        const panel = shell.panel as HTMLElement, host = shell.root.parentElement as HTMLElement;
        const style = getComputedStyle(panel);
        return { width: panel.getBoundingClientRect().width, height: panel.getBoundingClientRect().height,
            hostWidth: host.clientWidth, hostHeight: host.clientHeight,
            background: style.backgroundColor, opacity: style.opacity };
    });
    const initial = await state();
    assert.ok(Math.abs(initial.width - initial.hostWidth * 0.86) < 1);
    assert.ok(Math.abs(initial.height - Math.min(initial.hostHeight * 0.88, initial.hostHeight - 96)) < 1);
    assert.equal(initial.background, "rgba(18, 18, 22, 0.92)");
    assert.equal(initial.opacity, "0.99");
    for (const opacity of [0.90, 0.70, 0.99]) {
        await page.getByTitle("Toggle opacity", { exact: true }).click();
        const current = await state();
        assert.equal(current.background, initial.background);
        assert.equal(current.opacity, String(opacity), "Cycle all three whole-card opacity levels and return to the default");
    }
    await page.getByTitle("Toggle opacity", { exact: true }).click();
    await page.getByTitle("Dock panel (Split)", { exact: true }).click();
    assert.equal((await state()).opacity, "0.9");
    await page.getByTitle("Float panel", { exact: true }).click();
    assert.equal((await state()).opacity, "0.9");
    await page.getByTitle("Toggle opacity", { exact: true }).click();
    await page.getByTitle("Toggle opacity", { exact: true }).click();

    const restore = await page.evaluate(() => {
        const host = (window as any).__controller.sharedShell.root.parentElement as HTMLElement;
        const original = { width: host.style.width, height: host.style.height };
        host.style.width = "600px"; host.style.height = "440px";
        return original;
    });
    await page.waitForFunction(() => {
        const shell = (window as any).__controller.sharedShell;
        return Math.abs(shell.panel.getBoundingClientRect().width - 600 * 0.86) < 1
            && Math.abs(shell.panel.getBoundingClientRect().height - (440 - 96)) < 1;
    });
    await page.evaluate(restore => {
        const host = (window as any).__controller.sharedShell.root.parentElement as HTMLElement;
        Object.assign(host.style, restore);
    }, restore);
    await page.waitForFunction(initial => {
        const panel = (window as any).__controller.sharedShell.panel as HTMLElement;
        return Math.abs(panel.getBoundingClientRect().width - initial.width) < 1
            && Math.abs(panel.getBoundingClientRect().height - initial.height) < 1;
    }, initial);
    // Leave the next workflow at the unlocked default, as a fresh shell is.
    await page.getByTitle("Unlock background (Ambient)", { exact: true }).click();
}
