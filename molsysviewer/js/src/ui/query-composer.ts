export type QuerySyntax = "MolSysMT" | "Indices";

export type QueryPreview = {
    request_id?: number;
    status?: "pending";
    ok?: boolean;
    count?: number;
    error_message?: string;
};

export class ManualQueryComposer {
    private static nextRequestId = 1_000_000;
    private expression = "";
    private syntax: QuerySyntax = "MolSysMT";
    private preview: QueryPreview | null = null;
    private readonly root: HTMLDivElement;
    private readonly input: HTMLInputElement;
    private readonly syntaxSelect: HTMLSelectElement;
    private readonly status: HTMLDivElement;
    private readonly checkButton: HTMLButtonElement;
    private activeRequestId: number | null = null;

    constructor(
        private readonly scope: string,
        private readonly onRequest: (details: {
            request_id: number;
            expression: string;
            syntax: QuerySyntax;
        }) => void,
        private readonly onChange?: () => void,
        options?: {
            buttonLabel?: string;
            hideSyntax?: boolean;
            middleElement?: HTMLElement;
        }
    ) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-query-composer", scope);
        Object.assign(this.root.style, {
            display: "flex",
            flexDirection: "column",
            gap: "6px",
        });

        const row = document.createElement("div");
        Object.assign(row.style, {
            display: "flex",
            gap: "6px",
            alignItems: "center",
        });

        this.input = document.createElement("input");
        this.input.type = "text";
        this.input.placeholder = 'molecule_type=="protein"';
        this.input.setAttribute("data-molsysviewer-query-input", scope);
        Object.assign(this.input.style, {
            flex: "1 1 0",
            minWidth: "0",
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "6px 8px",
            color: "#fff",
            fontSize: "11px",
            outline: "none",
        });
        this.input.addEventListener("input", () => {
            this.expression = this.input.value;
            this.preview = null;
            this.activeRequestId = null;
            this.renderStatus();
            this.onChange?.();
        });
        this.input.addEventListener("keydown", (event) => {
            if (event.key !== "Enter") return;
            event.preventDefault();
            event.stopPropagation();
            this.check();
        });

        this.checkButton = document.createElement("button");
        this.checkButton.type = "button";
        this.checkButton.textContent = options?.buttonLabel ?? "Check";
        this.checkButton.setAttribute("data-molsysviewer-query-check", scope);
        Object.assign(this.checkButton.style, {
            flex: "0 0 auto",
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "6px 9px",
            color: "#f4f4f5",
            fontSize: "11px",
            fontWeight: "600",
            cursor: "pointer",
        });
        this.checkButton.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.check();
        });

        this.syntaxSelect = document.createElement("select");
        this.syntaxSelect.setAttribute("data-molsysviewer-query-syntax", scope);
        Object.assign(this.syntaxSelect.style, {
            flex: "0 0 auto",
            background: "rgba(0,0,0,0.2)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "6px",
            padding: "6px 8px",
            color: "#f4f4f5",
            fontSize: "11px",
            outline: "none",
        });
        for (const value of ["MolSysMT", "Indices"] as const) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            this.syntaxSelect.appendChild(option);
        }
        this.syntaxSelect.addEventListener("change", () => {
            this.syntax = this.syntaxSelect.value === "Indices" ? "Indices" : "MolSysMT";
            this.input.placeholder = this.syntax === "Indices" ? "0, 1, 2" : 'molecule_type=="protein"';
            this.preview = null;
            this.activeRequestId = null;
            this.renderStatus();
            this.onChange?.();
        });

        row.appendChild(this.input);
        if (options?.middleElement) {
            row.appendChild(options.middleElement);
        }
        row.appendChild(this.checkButton);
        if (!options?.hideSyntax) {
            row.appendChild(this.syntaxSelect);
        }
        this.root.appendChild(row);

        this.status = document.createElement("div");
        this.status.setAttribute("data-molsysviewer-query-status", scope);
        Object.assign(this.status.style, {
            minHeight: "14px",
            fontSize: "10px",
            color: "rgba(244,244,245,0.56)",
        });
        this.root.appendChild(this.status);
        this.renderStatus();
    }

    element(): HTMLDivElement {
        return this.root;
    }

    value(): { expression: string; syntax: QuerySyntax } {
        return { expression: this.expression.trim(), syntax: this.syntax };
    }

    setExpression(expression: string, syntax?: QuerySyntax): void {
        this.expression = expression;
        this.input.value = expression;
        if (syntax) {
            this.syntax = syntax;
            this.syntaxSelect.value = syntax;
            this.input.placeholder = syntax === "Indices" ? "0, 1, 2" : 'molecule_type=="protein"';
        }
        this.preview = null;
        this.activeRequestId = null;
        this.renderStatus();
        this.onChange?.();
    }

    isVerifiedNonEmpty(): boolean {
        return this.preview?.ok === true && Number(this.preview.count ?? 0) > 0;
    }

    updatePreview(preview: QueryPreview): boolean {
        if (
            this.activeRequestId === null
            || preview.request_id !== this.activeRequestId
        ) {
            return false;
        }
        this.preview = preview;
        this.renderStatus();
        return true;
    }

    private check(): void {
        const expression = this.expression.trim();
        if (!expression) {
            this.preview = null;
            this.activeRequestId = null;
            this.renderStatus();
            return;
        }
        const requestId = ManualQueryComposer.nextRequestId++;
        this.activeRequestId = requestId;
        this.preview = { request_id: requestId, status: "pending" };
        this.renderStatus();
        this.onRequest({
            request_id: requestId,
            expression,
            syntax: this.syntax,
        });
    }

    private renderStatus(): void {
        if (!this.expression.trim()) {
            this.status.textContent = "Enter a query, then press Enter or Check.";
            this.status.setAttribute("data-molsysviewer-query-status-value", "idle");
            this.status.style.color = "rgba(244,244,245,0.56)";
        } else if (this.preview?.status === "pending") {
            this.status.textContent = "Checking query...";
            this.status.setAttribute("data-molsysviewer-query-status-value", "pending");
            this.status.style.color = "rgba(244,244,245,0.72)";
        } else if (this.preview?.ok === true) {
            const count = Number(this.preview.count ?? 0);
            this.status.textContent = count === 1 ? "✓ 1 atom" : `✓ ${count} atoms`;
            this.status.setAttribute("data-molsysviewer-query-status-value", count > 0 ? "ok" : "empty");
            this.status.style.color = count > 0 ? "#86efac" : "#facc15";
        } else if (this.preview?.ok === false) {
            this.status.textContent = `✗ ${this.preview.error_message ?? "invalid syntax"}`;
            this.status.setAttribute("data-molsysviewer-query-status-value", "error");
            this.status.style.color = "#fca5a5";
        } else {
            this.status.textContent = "Press Enter or Check to verify.";
            this.status.setAttribute("data-molsysviewer-query-status-value", "idle");
            this.status.style.color = "rgba(244,244,245,0.56)";
        }
    }
}
