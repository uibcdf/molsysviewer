import type { PanelContext, StudioPanel } from "./types";
import { SystemLoadControls } from "./system-load-controls";
import { makeButton, makeSectionHeader } from "./ui-helpers";
import type { SystemFileBrowseResult } from "../../messages/viewer-messages";

/** Molecular input workspace; scientific loading remains owned by view.load(). */
export class LoadPanel implements StudioPanel {
    readonly key = "load";
    private controls?: SystemLoadControls;
    private inspect?: HTMLButtonElement;

    constructor(private readonly ctx: PanelContext, private readonly onInspect: () => void) {}

    mount(host: HTMLElement): void {
        Object.assign(host.style, { overflowY: "hidden", gap: "6px" });
        host.appendChild(makeSectionHeader("Load systems"));
        this.controls = new SystemLoadControls(this.ctx);
        host.appendChild(this.controls.root);
        this.inspect = makeButton("Inspect system", this.onInspect);
        this.inspect.setAttribute("data-molsysviewer-load-inspect", "true");
        this.inspect.style.display = "none";
        this.inspect.style.flex = "0 0 auto";
        host.appendChild(this.inspect);
    }

    setVisible(_visible: boolean): void {}
    open(): void { this.controls?.open(); }
    isPending(): boolean { return this.controls?.isPending() ?? false; }
    setSystemAvailable(available: boolean): void {
        this.controls?.setSystemAvailable(available);
        if (this.inspect) this.inspect.style.display = available ? "" : "none";
    }
    updateFiles(result: SystemFileBrowseResult): void { this.controls?.updateFiles(result); }
    updateResult(requestId: string, ok: boolean, atoms?: number, structures?: number, sources?: number, error?: string): boolean {
        return this.controls?.updateResult(requestId, ok, atoms, structures, sources, error) ?? false;
    }
}
