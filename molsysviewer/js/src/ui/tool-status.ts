export type ToolStatusState =
    | { action: null }
    | {
        action: "distance" | "angle" | "dihedral";
        pickedCount: number;
        requiredPicks: number;
        remainingPicks: number;
    };

function actionLabel(action: "distance" | "angle" | "dihedral"): string {
    switch (action) {
        case "distance": return "Distance";
        case "angle": return "Angle";
        case "dihedral": return "Dihedral";
    }
}

export class ToolStatusOverlay {
    private readonly root: HTMLDivElement;

    constructor(private readonly host: HTMLElement) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-tool-status", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            left: "14px",
            top: "14px",
            display: "none",
            maxWidth: "280px",
            padding: "10px 12px",
            borderRadius: "12px",
            border: "1px solid rgba(255,255,255,0.16)",
            background: "rgba(18, 18, 22, 0.92)",
            color: "#f4f4f5",
            boxShadow: "0 12px 28px rgba(0,0,0,0.28)",
            zIndex: "18",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "12px",
            lineHeight: "1.4",
            pointerEvents: "none",
        });
        this.host.appendChild(this.root);
    }

    update(state: ToolStatusState): void {
        if (state.action === null) {
            this.root.style.display = "none";
            this.root.replaceChildren();
            return;
        }

        const title = document.createElement("div");
        title.textContent = `${actionLabel(state.action)} tool`;
        Object.assign(title.style, {
            fontWeight: "700",
            marginBottom: "4px",
        });

        const detail = document.createElement("div");
        detail.textContent = `Pick ${state.remainingPicks} more atom${state.remainingPicks === 1 ? "" : "s"} (${state.pickedCount}/${state.requiredPicks})`;
        detail.style.opacity = "0.95";

        const hint = document.createElement("div");
        hint.textContent = "Esc cancels";
        Object.assign(hint.style, {
            marginTop: "6px",
            opacity: "0.72",
            fontSize: "11px",
        });

        this.root.replaceChildren(title, detail, hint);
        this.root.style.display = "block";
    }

    dispose(): void {
        this.root.remove();
    }
}
