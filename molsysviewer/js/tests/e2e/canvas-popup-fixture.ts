import type { Page } from "playwright";
import type { PythonFixtureBridge } from "./python-fixture-bridge";

// Playwright bindings live for the page lifetime. Keep one binding and release
// its current worker owner between scenarios, including navigation on that page.
const boundPages = new WeakSet<Page>();
const activeFixtures = new WeakMap<Page, PythonFixtureBridge>();

/** Only the notebook comm/trait transport is adapted; the Python authority is real. */
export async function mountCanvasPopupFixture(page: Page, bridge: PythonFixtureBridge,
    options: { trajectoryLabel?: string | null } = {}) {
        const fixture = await bridge.request();
        await page.goto("about:blank");
        await page.setContent('<div id="notebook" style="width:850px;height:600px"></div>');
        activeFixtures.set(page, bridge);
        if (!boundPages.has(page)) {
            await page.exposeFunction("__popupFixtureRequest", (message: unknown) => {
                const owner = activeFixtures.get(page);
                if (!owner) throw new Error("Canvas popup fixture transport has no live owner");
                return owner.request([message]);
            });
            boundPages.add(page);
        }
        await page.evaluate(async fixture => {
            const w = window as any;
            const traits = fixture.traits;
            // Legacy notebook state must not override the runtime actually loaded.
            traits.popup_js_source = 'throw new Error("obsolete popup runtime selected");';
            const listeners = new Map<string, Set<(...args: any[]) => void>>();
            let queue = Promise.resolve();
            const model = w.__popupWidgetModel = {
                get: (key: string) => traits[key],
                set(key: string, value: unknown) {
                    if (JSON.stringify(traits[key]) === JSON.stringify(value)) return;
                    traits[key] = value;
                    for (const callback of listeners.get(`change:${key}`) || []) callback();
                },
                on(event: string, callback: (...args: any[]) => void) {
                    if (!listeners.has(event)) listeners.set(event, new Set());
                    listeners.get(event)!.add(callback);
                },
                off(event: string, callback: (...args: any[]) => void) { listeners.get(event)?.delete(callback); },
                save_changes() {
                    model.send({ review_traits: Object.fromEntries([
                        "viewer_mode", "controls_mode", "panel_mode_style", "show_controls", "autohide_controls",
                        "autohide_scope", "controls_position", "controls_position_fullscreen",
                    ].map(trait => [trait, traits[trait]])) });
                },
                send(message: unknown) {
                    queue = queue.then(async () => {
                        const result = await w.__popupFixtureRequest(message);
                        // Simulate only the notebook transport, with real Python responses.
                        for (const { content, buffers } of result.messages) {
                            const views = buffers.map((encoded: string) => new DataView(
                                Uint8Array.from(atob(encoded), char => char.charCodeAt(0)).buffer));
                            for (const callback of listeners.get("msg:custom") || []) callback(content, views);
                        }
                    }).catch(error => { errors.push(String(error)); console.error(error); });
                },
            };
            const errors = w.__popupFixtureErrors = [];
            w.__popupFixtureDrain = async () => {
                // Responses may enqueue further stream acknowledgments.
                while (true) {
                    const pending = queue;
                    await pending;
                    if (pending === queue) return;
                }
            };
            const url = URL.createObjectURL(new Blob([traits._esm], { type: "text/javascript" }));
            try {
                const bootstrap = await import(url);
                w.__popupWidgetDispose = await bootstrap.default.render({ model, el: document.getElementById("notebook") });
            } finally { URL.revokeObjectURL(url); }
        }, fixture);
        const trajectoryLabel = options.trajectoryLabel === undefined ? "1 / 3" : options.trajectoryLabel;
        if (trajectoryLabel !== null) {
            await page.waitForFunction(label => document.querySelector('[data-molsysviewer-trajectory-label="true"]')?.textContent === label, trajectoryLabel);
        } else {
            await page.waitForFunction(() => !!document.querySelector("canvas"));
            await page.evaluate(() => (window as any).__popupFixtureDrain());
        }
        return async () => {
            if (activeFixtures.get(page) === bridge) activeFixtures.delete(page);
        };
}

/** Observe real controllers without replacing molecular or rendering operations. */
export async function captureCanvasPopupControllers(page: Page, waitForController = true) {
    await page.evaluate(() => {
        const w=window as any;
        const C=w.__molsysviewer_anywidget_runtime__?.module.MolSysViewerController;
        if (C) {
            for (const method of ["getCameraSnapshot", "togglePanelMode"]) {
                const operation=C.prototype[method];
                C.prototype[method]=function(...args:any[]) { w.__mirrorController=this; return operation.apply(this,args); };
            }
        } else w.__mirrorController = w.__molsysviewerDocsController;
        const open=window.open.bind(window);
        window.open=((...args:any[])=>{
            const win:any=open(...args);
            const append=win.Node.prototype.appendChild;
            win.Node.prototype.appendChild=function(node:any) {
                if(node.tagName==='SCRIPT' && node.textContent.includes('await boot(module)')) {
                    node.textContent=node.textContent.replace('await boot(module)', `const create=module.MolSysViewerController.create;
                        module.MolSysViewerController.create=async function(...args) {
                            const ctrl=await create.apply(this,args); window.__mirrorController=ctrl; return ctrl;
                        }; await boot(module)`);
                }
                return append.call(this,node);
            };
            return win;
        }) as typeof window.open;
    });
    if (waitForController) await page.waitForFunction(()=>!!(window as any).__mirrorController);
}
