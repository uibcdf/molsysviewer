export interface RemoteUploadResult {
    filename: string;
    nAtoms: number;
    nStructures: number;
}

/** Small Mol*-free file picker whose transport is supplied by the session host. */
export class RemoteFileControls {
    readonly root: HTMLDivElement;
    readonly input: HTMLInputElement;
    private readonly button: HTMLButtonElement;
    private readonly status: HTMLSpanElement;

    constructor(
        host: HTMLElement,
        private readonly upload: (file: File) => Promise<RemoteUploadResult>,
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-remote-files", "true");
        Object.assign(this.root.style, {
            position: "absolute", top: "14px", left: "14px", zIndex: "3",
            display: "flex", alignItems: "center", gap: "8px", padding: "6px",
            borderRadius: "8px", border: "1px solid rgba(255,255,255,.12)",
            background: "rgba(8,11,16,.78)", color: "#f5f7fa", pointerEvents: "auto",
            font: "11px/1.2 system-ui,sans-serif",
        });
        this.input = document.createElement("input");
        this.input.type = "file";
        this.input.accept = ".pdb,.ent,.cif,.mmcif,.gro,.mol2,.sdf,.h5msm";
        this.input.setAttribute("data-molsysviewer-upload-input", "true");
        this.input.style.display = "none";
        this.button = document.createElement("button");
        this.button.type = "button";
        this.button.textContent = "Open molecular file…";
        this.button.setAttribute("data-molsysviewer-upload-button", "true");
        Object.assign(this.button.style, {
            padding: "5px 8px", borderRadius: "6px", border: "1px solid rgba(255,255,255,.18)",
            background: "rgba(18,18,22,.9)", color: "#f5f7fa", cursor: "default",
        });
        this.status = document.createElement("span");
        this.status.setAttribute("data-molsysviewer-upload-status", "idle");
        this.status.textContent = "";

        this.button.addEventListener("click", () => this.input.click());
        this.input.addEventListener("change", () => {
            const file = this.input.files?.[0];
            if (file) void this.submit(file);
        });
        this.root.append(this.input, this.button, this.status);
        host.appendChild(this.root);
    }

    dispose(): void {
        this.root.remove();
    }

    private async submit(file: File): Promise<void> {
        this.button.disabled = true;
        this.status.setAttribute("data-molsysviewer-upload-status", "uploading");
        this.status.textContent = `Uploading ${file.name}…`;
        try {
            const result = await this.upload(file);
            this.status.setAttribute("data-molsysviewer-upload-status", "loaded");
            this.status.textContent = `${result.filename}: ${result.nAtoms} atoms · ${result.nStructures} frame${result.nStructures === 1 ? "" : "s"}`;
        } catch (error) {
            this.status.setAttribute("data-molsysviewer-upload-status", "failed");
            this.status.textContent = error instanceof Error ? error.message : String(error);
        } finally {
            this.button.disabled = false;
            this.input.value = "";
        }
    }
}
