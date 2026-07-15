// Shared, stateless DOM builders for the Studio subpanels.
//
// These are pure functions (no `this`, no shared state): each returns a fresh
// element. They are the common vocabulary every subpanel module reuses so the
// panels look and behave identically. Extracted from `group-panel.ts` as the
// first step of the panel-per-module refactor.

export function formatUnitLabel(unit: string): string {
    switch (unit.trim().toLowerCase()) {
        case "angstrom":
        case "angstroms":
            return "Å";
        case "nanometer":
        case "nanometers":
            return "nm";
        case "degree":
        case "degrees":
            return "°";
        case "radian":
        case "radians":
            return "rad";
        default:
            return unit;
    }
}

export function makeSectionHeader(title: string): HTMLDivElement {
    const header = document.createElement("div");
    Object.assign(header.style, {
        fontSize: "13px",
        fontWeight: "700",
        color: "#f4f4f5",
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        position: "relative",
        width: "100%",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        paddingBottom: "6px",
        marginBottom: "6px",
    });

    const text = document.createElement("span");
    text.textContent = title;
    header.appendChild(text);

    return header;
}

export function makeButton(text: string, onClick: () => void): HTMLButtonElement {
    const btn = document.createElement("button");
    btn.textContent = text;
    Object.assign(btn.style, {
        flex: "1 1 0",
        background: "rgba(255,255,255,0.06)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "6px",
        padding: "5px 8px",
        color: "#f4f4f5",
        fontSize: "11px",
        fontWeight: "600",
        cursor: "pointer",
        transition: "all 0.15s ease",
        textAlign: "center",
    });
    btn.addEventListener("mouseenter", () => {
        btn.style.background = "rgba(255,255,255,0.12)";
        btn.style.border = "1px solid rgba(255,255,255,0.16)";
    });
    btn.addEventListener("mouseleave", () => {
        btn.style.background = "rgba(255,255,255,0.06)";
        btn.style.border = "1px solid rgba(255,255,255,0.1)";
    });
    btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
    });
    return btn;
}

export function makeRowElement(
    titleText: string,
    subtitleText: string,
    onActivate?: () => void,
    onDelete?: () => void,
    visibility?: { hidden?: boolean; onToggleVisibility?: (hidden: boolean) => void },
    onStyle?: () => void,
): HTMLDivElement {
    const row = document.createElement("div");
    row.setAttribute("data-molsysviewer-group-panel-row", "true");
    row.setAttribute("data-molsysviewer-group-panel-summary-item", "true");
    Object.assign(row.style, {
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "6px 10px",
        borderRadius: "8px",
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.06)",
        gap: "8px",
        transition: "background 0.1s ease",
    });

    // Hover effect
    row.addEventListener("mouseenter", () => {
        row.style.background = "rgba(255,255,255,0.09)";
    });
    row.addEventListener("mouseleave", () => {
        row.style.background = "rgba(255,255,255,0.05)";
    });

    // Clickable main area
    const main = document.createElement("div");
    Object.assign(main.style, {
        display: "flex",
        flexDirection: "column",
        gap: "2px",
        flex: "1 1 0",
        minWidth: "0",
        cursor: onActivate ? "pointer" : "default",
    });
    if (onActivate) {
        row.style.cursor = "pointer";
        row.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onActivate();
        });
    }

    const title = document.createElement("div");
    Object.assign(title.style, {
        fontSize: "12px",
        fontWeight: "600",
        color: "#f4f4f5",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
    });
    title.textContent = titleText;

    const subtitle = document.createElement("div");
    Object.assign(subtitle.style, {
        fontSize: "10px",
        color: "rgba(244,244,245,0.56)",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
    });
    subtitle.textContent = subtitleText;

    main.appendChild(title);
    main.appendChild(subtitle);
    row.appendChild(main);

    // Actions toolbar (Right side)
    const actions = document.createElement("div");
    Object.assign(actions.style, {
        display: "flex",
        alignItems: "center",
        gap: "6px",
        flex: "0 0 auto",
    });
    row.appendChild(actions);

    // Style / Paint Button
    if (onStyle) {
        const styleBtn = document.createElement("button");
        styleBtn.type = "button";
        styleBtn.textContent = "🎨";
        styleBtn.title = "Style & Color";
        Object.assign(styleBtn.style, {
            background: "transparent",
            border: "0",
            color: "rgba(244,244,245,0.55)",
            fontSize: "11px",
            cursor: "pointer",
            padding: "2px 6px",
            borderRadius: "4px",
        });
        styleBtn.addEventListener("mouseenter", () => {
            styleBtn.style.color = "#10b981";
        });
        styleBtn.addEventListener("mouseleave", () => {
            styleBtn.style.color = "rgba(244,244,245,0.55)";
        });
        styleBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onStyle();
        });
        actions.appendChild(styleBtn);
    }

    // Visibility Toggle (Eye icon)
    if (visibility?.onToggleVisibility) {
        const eyeBtn = document.createElement("button");
        eyeBtn.type = "button";
        eyeBtn.textContent = visibility.hidden ? "⦻" : "👁";
        eyeBtn.title = visibility.hidden ? "Show" : "Hide";
        Object.assign(eyeBtn.style, {
            background: "transparent",
            border: "0",
            color: visibility.hidden ? "rgba(244,244,245,0.36)" : "#6366f1",
            fontSize: "12px",
            cursor: "pointer",
            padding: "2px 6px",
            borderRadius: "4px",
        });
        eyeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            visibility.onToggleVisibility?.(!visibility.hidden);
        });
        actions.appendChild(eyeBtn);
    }

    // Delete Button (Trash/X icon)
    if (onDelete) {
        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.textContent = "✕";
        delBtn.title = "Delete";
        Object.assign(delBtn.style, {
            background: "transparent",
            border: "0",
            color: "rgba(244,244,245,0.48)",
            fontSize: "12px",
            cursor: "pointer",
            padding: "2px 6px",
            borderRadius: "4px",
            transition: "color 0.1s ease",
        });
        delBtn.addEventListener("mouseenter", () => {
            delBtn.style.color = "#ef4444";
        });
        delBtn.addEventListener("mouseleave", () => {
            delBtn.style.color = "rgba(244,244,245,0.48)";
        });
        delBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            onDelete();
        });
        actions.appendChild(delBtn);
    }
    return row;
}

export function makeSettingsCard(titleText: string): HTMLDivElement {
    const card = document.createElement("div");
    Object.assign(card.style, {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        padding: "10px",
        borderRadius: "8px",
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.05)",
    });

    const header = document.createElement("div");
    Object.assign(header.style, {
        fontSize: "11px",
        fontWeight: "700",
        color: "rgba(244,244,245,0.48)",
        textTransform: "uppercase",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        paddingBottom: "4px",
        marginBottom: "2px",
    });
    header.textContent = titleText;
    card.appendChild(header);

    return card;
}

export function makeStyledSelect(
    options: Array<string | { value: string; label: string }>,
    selectedValue: string,
    onChange: (value: string) => void,
): HTMLSelectElement {
    const select = document.createElement("select");
    Object.assign(select.style, {
        background: "rgba(0,0,0,0.28)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: "6px",
        padding: "3px 6px",
        color: "#f4f4f5",
        fontSize: "11px",
        fontWeight: "500",
        outline: "none",
        cursor: "pointer",
    });

    for (const opt of options) {
        const value = typeof opt === "string" ? opt : opt.value;
        const label = typeof opt === "string" ? opt : opt.label;
        const el = document.createElement("option");
        el.value = value;
        el.textContent = label;
        el.selected = value === selectedValue;
        select.appendChild(el);
    }
    select.value = selectedValue;

    select.addEventListener("change", () => {
        onChange(select.value);
    });

    return select;
}

export function makeCheckboxRow(
    labelText: string,
    checked: boolean,
    onChange: (checked: boolean) => void,
): HTMLDivElement {
    const row = document.createElement("div");
    Object.assign(row.style, {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        width: "100%",
        cursor: "pointer",
    });

    const label = document.createElement("span");
    label.textContent = labelText;
    Object.assign(label.style, { fontSize: "11px", color: "rgba(244,244,245,0.8)" });
    row.appendChild(label);

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = checked;
    Object.assign(cb.style, {
        cursor: "pointer",
        outline: "none",
    });

    const toggle = () => {
        cb.checked = !cb.checked;
        onChange(cb.checked);
    };

    row.addEventListener("click", (e) => {
        if (e.target !== cb) {
            e.preventDefault();
            toggle();
        }
    });
    cb.addEventListener("change", () => {
        onChange(cb.checked);
    });

    row.appendChild(cb);
    return row;
}
