import type { Locator, Page } from "playwright";

/** Stall genuine scientific replies only on the actual Save click. */
export async function armMovingDependencyHold(save: Locator) {
    await save.evaluate(button => {
        button.addEventListener("click", () => {
            let host: any = window;
            for (let depth = 0; depth < 3 && host && !host.__popupWidgetModel; depth++) host = host.opener;
            if (!host?.__popupWidgetModel) throw new Error("Save has no real widget authority");
            const monitor = host.__movingCapture;
            if (monitor.activeCapture) monitor.activeCapture.holdArmedAt = host.performance.now();
            void host.__popupWidgetModel.send({ moving_fixture: "hold" }).catch((error: any) => {
                monitor.holdError = String(error);
                if (monitor.activeCapture) monitor.activeCapture.holdError = String(error);
            });
        }, { capture: true, once: true });
    });
}

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
