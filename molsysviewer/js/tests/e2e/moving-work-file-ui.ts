import type { Page } from "playwright";

export async function movingEndpointIdentity(page: Page): Promise<string> {
    return page.evaluate(() => (window as any).molsysviewer_popup_channel?.popupEndpointId ?? "primary");
}

export async function openMovingWorkFile(page: Page) {
    await page.bringToFront();
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
