import type { Locator, Page } from "playwright";

/** Establish real pending science before Save, without invalidating a good frame. */
export async function holdMovingDependency(canvas: Page, save?: Locator) {
    // UI actionability precedes the deliberate stall. A coherent capture need
    // not generate a query, so holding only at click time is insufficient.
    if (save) await save.click({ trial: true });
    await canvas.evaluate(async () => {
        let host: any = window;
        for (let depth = 0; depth < 3 && host && !host.__popupWidgetModel; depth++) host = host.opener;
        if (!host?.__popupWidgetModel) throw new Error("Save has no real widget authority");
        const monitor = host.__movingCapture;
        monitor.heldSource = null;
        if (monitor.activeCapture) monitor.activeCapture.holdArmedAt = host.performance.now();
        await host.__popupWidgetModel.send({ moving_fixture: "hold" });
    });
    await canvas.waitForFunction(() => {
        const w = window as any, c = w.__mirrorController;
        const authority = w.__popupWidgetModel ? w : window.opener;
        return authority.__movingCapture.heldSource?.count > 0
            && c.dynamicRegionEvaluationInFlight !== null;
    });
}

export async function movingEndpointIdentity(page: Page): Promise<string> {
    return page.evaluate(() => (window as any).molsysviewer_popup_channel?.popupEndpointId ?? "primary");
}

export async function openMovingWorkFile(page: Page) {
    await page.bringToFront();
    // A new popup may still be about:blank: an absent loading indicator is
    // already "hidden". Observe its actual role and usable owner before
    // choosing panel-only navigation or molecular-controller operations.
    await page.waitForFunction(() => {
        const w = window as any;
        if (w.molsysviewer_init_options?.isPanelOnly) {
            return Array.from(document.querySelectorAll('select[aria-label="Studio section"], [data-molsysviewer-group-panel-tab="export"]'))
                .some(element => {
                    const bounds = element.getBoundingClientRect();
                    return bounds.width > 0 && bounds.height > 0 && getComputedStyle(element).visibility !== "hidden";
                });
        }
        return !!w.__mirrorController?.groupPanel;
    });
    if (await page.evaluate(() => !!(window as any).molsysviewer_init_options?.isPanelOnly)) {
        const navigation = page.getByLabel("Studio section", { exact: true });
        if (await navigation.isVisible()) await navigation.selectOption("export");
        else await page.locator('[data-molsysviewer-group-panel-tab="export"]').click();
    } else {
        await page.evaluate(() => {
            const controller = (window as any).__mirrorController;
            controller.setPanelMode("navigate", true);
            controller.groupPanel.openSection("export");
        });
    }
    const work = page.locator('[data-molsysviewer-work-files]');
    await work.waitFor({ state: "visible" });
    return work;
}
