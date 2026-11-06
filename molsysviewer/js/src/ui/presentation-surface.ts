/** Independent View presentation; molecular data stay in each View's own model. */
type Destination = "notebook" | "window";
type OpenResult = (id: string, destination: Destination) => Promise<void>;
const surfaces = new Map<string, OpenResult>();

export function presentResult(hostId: string, id: string, destination: Destination): Promise<void> {
    const open = surfaces.get(hostId);
    if (!open) return Promise.reject(new Error("The notebook output is unavailable. Display the source View again."));
    return open(id, destination);
}

export const presentationSurface = {
    async render({ model, el }: { model: any; el: HTMLElement }) {
        el.dataset.molsysviewerPresentationSurface = "true";
        const manager = model.widget_manager;
        if (!manager?.get_model || !manager?.create_view) throw new Error("This notebook cannot present child widgets.");
        const sourceHost = document.createElement("div");
        const resultsHost = document.createElement("div");
        el.append(sourceHost, resultsHost);
        const sourceModel = await manager.get_model(model.get("source_id"));
        const sourceView = await manager.create_view(sourceModel);
        sourceHost.appendChild(sourceView.el);
        sourceView.trigger?.("displayed");
        const id = model.model_id || sourceModel.get("presentation_host_id");
        let disposed = false, sequence = 0, queue = Promise.resolve();
        const entries = new Map<string, any>();
        const reservations = new Map<string, Window>();
        const requests = new Map<number, { resolve(): void; reject(error: Error): void; timer: any }>();

        async function popupApi(element: HTMLElement, selector: string): Promise<any> {
            const deadline = Date.now() + 30000;
            while (!disposed && Date.now() < deadline) {
                const api = element.matches(selector) ? element : element.querySelector(selector);
                if (typeof (api as any)?.molsysviewerOpenPopup === "function") return api;
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            throw new Error("The result canvas is not ready. Try opening it again.");
        }
        (el as any).molsysviewerOpenPopup = async (win: Window) => {
            const api = await popupApi(sourceView.el, "[data-molsysviewer-canvas-output]");
            api.molsysviewerOnPopupClosed = () => (el as any).molsysviewerOnPopupClosed?.();
            return api.molsysviewerOpenPopup(win);
        };

        const open: OpenResult = (resultId, destination) => {
            if (disposed) return Promise.reject(new Error("The notebook output has been removed."));
            if (destination !== "notebook" && destination !== "window") return Promise.reject(new Error("Choose notebook or window."));
            if (destination === "window") {
                const existing = entries.get(resultId)?.win;
                const win = existing && !existing.closed ? existing : window.open("", "_blank", "width=960,height=720");
                if (!win) return Promise.reject(new Error("The browser blocked the window. Allow popups and try again; the result is retained."));
                if (!existing || existing.closed) {
                    win.document.title = "Molecular result";
                    win.document.body.textContent = "Opening molecular result…";
                }
                win.focus();
                reservations.set(resultId, win);
            }
            const request = ++sequence;
            return new Promise<void>((resolve, reject) => {
                const timer = setTimeout(() => {
                    requests.delete(request);
                    const win = reservations.get(resultId);
                    if (win && !entries.get(resultId)?.win) win.close();
                    reservations.delete(resultId);
                    reject(new Error("Presentation did not complete. The result can be recovered from Python."));
                }, 60000);
                requests.set(request, { resolve, reject, timer });
                model.send({ type: "show", id: resultId, destination, request_id: request });
            });
        };
        surfaces.set(id, open);

        async function synchronize() {
            if (disposed) return;
            const items = model.get("items") || [];
            const live = new Set(items.map((item: any) => item.id));
            for (const [key, entry] of entries) if (!live.has(key)) {
                entry.view.remove(); entry.element.remove(); entry.win?.close(); entries.delete(key);
            }
            for (const item of items) {
                if (disposed) return;
                let entry = entries.get(item.id);
                try {
                    if (!entry) {
                        const widget = await manager.get_model(item.model_id);
                        const view = await manager.create_view(widget);
                        if (disposed || !(model.get("items") || []).some((value: any) => value.id === item.id)) {
                            view.remove(); continue;
                        }
                        const element = document.createElement("section");
                        element.dataset.molsysviewerResult = item.id;
                        const header = document.createElement("div");
                        header.style.cssText = "display:flex;align-items:center;gap:12px;padding:12px 0;font:14px system-ui";
                        const title = document.createElement("strong"); title.textContent = item.title;
                        const close = document.createElement("button"); close.textContent = "Close view";
                        close.style.cssText = "font:inherit;padding:5px 10px;border:1px solid #87909b;border-radius:6px;background:transparent;color:inherit;cursor:pointer";
                        close.onclick = () => model.send({ type: "close", id: item.id });
                        header.append(title, close); element.append(header, view.el); resultsHost.appendChild(element);
                        view.trigger?.("displayed");
                        entry = { view, element, destination: item.destination, win: null, request: Symbol() };
                        entries.set(item.id, entry);
                        await popupApi(view.el, "[data-molsysviewer-presentation-surface]");
                    }
                    if (entry.request === item.request_id) continue;
                    entry.request = item.request_id;
                    if (item.destination === "window") {
                        const win = reservations.get(item.id);
                        if (!win || win.closed) throw new Error("Click Open in new window to grant browser permission.");
                        reservations.delete(item.id);
                        if (!entry.win || entry.win.closed) {
                            // Keep the authority rendered at a real size. Its external
                            // canvas uses the same qualified popup transport as other Views.
                            entry.element.style.cssText = "position:fixed;left:-100000px;top:0;width:960px;height:520px";
                            const child = await popupApi(entry.view.el, "[data-molsysviewer-presentation-surface]");
                            await child.molsysviewerOpenPopup(win);
                            child.molsysviewerOnPopupClosed = () => {
                                if (!disposed) model.send({ type: "close", id: item.id });
                            };
                            entry.win = win;
                            win.document.title = item.title;
                        } else entry.win.focus();
                    } else entry.element.scrollIntoView({ block: "nearest" });
                    model.send({ type: "shown", id: item.id, request_id: item.request_id });
                } catch (error) {
                    reservations.get(item.id)?.close(); reservations.delete(item.id);
                    model.send({ type: "shown", id: item.id, request_id: item.request_id, error: String(error) });
                }
            }
            sourceHost.hidden = model.get("source_closed") === true;
        }
        const changed = () => { queue = queue.then(synchronize).catch(error => console.error("Result presentation failed", error)); };
        const response = (message: any) => {
            if (message?.type !== "response") return;
            const pending = requests.get(message.request_id);
            if (!pending) return;
            clearTimeout(pending.timer); requests.delete(message.request_id);
            if (message.error) pending.reject(new Error(message.error)); else pending.resolve();
        };
        model.on("change:items", changed); model.on("change:source_closed", changed); model.on("msg:custom", response);
        await synchronize();
        return () => {
            disposed = true;
            if (surfaces.get(id) === open) surfaces.delete(id);
            model.off("change:items", changed); model.off("change:source_closed", changed); model.off("msg:custom", response);
            for (const pending of requests.values()) { clearTimeout(pending.timer); pending.reject(new Error("The notebook output was removed.")); }
            for (const win of reservations.values()) win.close();
            for (const entry of entries.values()) { entry.win?.close(); entry.view.remove(); }
            sourceView.remove(); el.replaceChildren();
        };
    },
};
