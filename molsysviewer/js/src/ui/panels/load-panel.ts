import type { PanelContext, StudioPanel } from "./types";
import { SystemLoadControls } from "./system-load-controls";
import { makeButton, makeSectionHeader } from "./ui-helpers";

/** Molecular input workspace; scientific loading remains owned by view.load(). */
export class LoadPanel implements StudioPanel {
    readonly key = "load";
    private controls?: SystemLoadControls;
    private inspect?: HTMLButtonElement;

    constructor(private readonly ctx: PanelContext, private readonly onInspect: () => void) {}

    mount(host: HTMLElement): void {
        host.appendChild(makeSectionHeader("Load systems"));
        const intro = document.createElement("div");
        intro.textContent = "Load one system, add several, or combine topology and coordinates or a trajectory.";
        Object.assign(intro.style, { fontSize: "12px", lineHeight: "1.5", color: "rgba(244,244,245,0.75)" });
        host.appendChild(intro);
        this.controls = new SystemLoadControls(this.ctx);
        Object.assign(this.controls.root.style, { maxHeight: "none", overflowY: "visible", fontSize: "12px" });
        const summary = this.controls.root.querySelector("summary");
        if (summary) (summary as HTMLElement).style.display = "none";
        this.controls.open();
        host.appendChild(this.controls.root);
        this.inspect = makeButton("Inspect system", this.onInspect);
        this.inspect.setAttribute("data-molsysviewer-load-inspect", "true");
        this.inspect.style.display = "none";
        host.appendChild(this.inspect);
    }

    setVisible(_visible: boolean): void {}
    open(): void { this.controls?.open(); }
    isPending(): boolean { return this.controls?.isPending() ?? false; }
    setSystemAvailable(available: boolean): void {
        if (this.inspect) this.inspect.style.display = available ? "" : "none";
    }
    updateResult(requestId: string, ok: boolean, atoms?: number, structures?: number, sources?: number, error?: string): boolean {
        return this.controls?.updateResult(requestId, ok, atoms, structures, sources, error) ?? false;
    }
}
