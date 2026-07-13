import { makeStyledSelect } from "./ui-helpers";

export const FALLBACK_REPRESENTATIONS = [
    "backbone",
    "ball-and-stick",
    "cartoon",
    "carbohydrate",
    "ellipsoid",
    "gaussian-surface",
    "gaussian-volume",
    "label",
    "line",
    "molecular-surface",
    "point",
    "spacefill",
];

export const FALLBACK_PRESETS = [
    "atomic-detail",
    "auto",
    "coarse-surface",
    "empty",
    "polymer-and-ligand",
    "polymer-cartoon",
];

export const STRUCTURAL_COLOR_OPTIONS = [
    { value: "", label: "Keep current" },
    { value: "element_cpk", label: "Element (CPK)" },
    { value: "chain_default", label: "Chain" },
    { value: "secondary_structure_default", label: "Secondary structure" },
    { value: "physicochemical", label: "Physicochemical" },
    { value: "residue_name", label: "Residue name" },
    { value: "molecule_type", label: "Molecule type" },
    { value: "entity_default", label: "Entity" },
    { value: "illustrative_default", label: "Illustrative" },
    { value: "uniform", label: "Uniform color" },
];

export const QUALITY_OPTIONS = ["auto", "lowest", "lower", "low", "medium", "high", "higher", "highest", "custom"];

export function makeStyleControlRow(label: string, control: HTMLElement): HTMLDivElement {
    const row = document.createElement("div");
    Object.assign(row.style, {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "8px",
        width: "100%",
    });
    const text = document.createElement("span");
    text.textContent = label;
    Object.assign(text.style, {
        fontSize: "11px",
        color: "rgba(244,244,245,0.7)",
    });
    row.appendChild(text);
    row.appendChild(control);
    return row;
}

export type StyleDraftControls = {
    representationSelect: HTMLSelectElement;
    presetSelect: HTMLSelectElement;
    qualitySelect: HTMLSelectElement;
    opacityInput: HTMLInputElement;
    opacityValue: HTMLSpanElement;
    colorSchemeSelect: HTMLSelectElement;
    customColorInput: HTMLInputElement;
    representationRow: HTMLDivElement;
    presetRow: HTMLDivElement;
    qualityRow: HTMLDivElement;
    colorRow: HTMLDivElement;
    opacityRow: HTMLDivElement;
};

export function bindContinuousHistory(
    input: HTMLInputElement,
    onStart: () => void,
    onEnd: () => void,
): void {
    let active = false;
    const start = () => {
        if (active) return;
        active = true;
        onStart();
    };
    const end = () => {
        if (!active) return;
        active = false;
        onEnd();
    };
    input.addEventListener("pointerdown", start);
    input.addEventListener("focus", start);
    input.addEventListener("pointerup", end);
    input.addEventListener("pointercancel", end);
    input.addEventListener("blur", end);
    input.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === "Escape") end();
    });
}

export function createStyleDraftControls(options: {
    id: string;
    dataPrefix: string;
    representations: Array<string | { value: string; label: string }>;
    presets: Array<string | { value: string; label: string }>;
    currentRepresentation?: string | null;
    currentPreset?: string | null;
    params?: Record<string, unknown>;
    opacityDisabled?: boolean;
    opacityDisabledTitle?: string;
}): StyleDraftControls {
    const params = options.params ?? {};
    let representationSelect: HTMLSelectElement;
    let presetSelect: HTMLSelectElement;
    representationSelect = makeStyledSelect(
        options.representations,
        options.currentPreset ? "" : (options.currentRepresentation ?? ""),
        (value) => {
            if (value) presetSelect.value = "";
        },
    );
    representationSelect.setAttribute(`data-molsysviewer-${options.dataPrefix}-representation`, options.id);
    presetSelect = makeStyledSelect(
        [{ value: "", label: "No preset" }, ...options.presets],
        options.currentPreset ?? "",
        (value) => {
            if (value) representationSelect.value = "";
        },
    );
    presetSelect.setAttribute(`data-molsysviewer-${options.dataPrefix}-preset`, options.id);

    const opacityWrap = document.createElement("div");
    Object.assign(opacityWrap.style, {
        display: "flex",
        alignItems: "center",
        gap: "6px",
    });
    const opacityInput = document.createElement("input");
    opacityInput.type = "range";
    opacityInput.min = "0";
    opacityInput.max = "1";
    opacityInput.step = "0.05";
    opacityInput.value = String(typeof params.alpha === "number" ? params.alpha : 1);
    opacityInput.setAttribute(`data-molsysviewer-${options.dataPrefix}-opacity`, options.id);
    if (options.opacityDisabled) {
        opacityInput.disabled = true;
        opacityInput.title = options.opacityDisabledTitle ?? "";
    }
    const opacityValue = document.createElement("span");
    opacityValue.textContent = Number(opacityInput.value).toFixed(2);
    opacityValue.setAttribute(`data-molsysviewer-${options.dataPrefix}-opacity-value`, options.id);
    opacityInput.addEventListener("input", () => {
        opacityValue.textContent = Number(opacityInput.value).toFixed(2);
    });
    opacityWrap.appendChild(opacityInput);
    opacityWrap.appendChild(opacityValue);

    const qualitySelect = makeStyledSelect(
        QUALITY_OPTIONS,
        typeof params.quality === "string" ? params.quality : "auto",
        () => {},
    );
    qualitySelect.setAttribute(`data-molsysviewer-${options.dataPrefix}-quality`, options.id);

    const customColorInput = document.createElement("input");
    customColorInput.type = "color";
    customColorInput.value = "#3b82f6";
    customColorInput.setAttribute(`data-molsysviewer-${options.dataPrefix}-uniform-color`, options.id);
    Object.assign(customColorInput.style, {
        width: "24px",
        height: "24px",
        border: "1px solid rgba(255,255,255,0.25)",
        borderRadius: "4px",
        padding: "0",
        background: "transparent",
        cursor: "pointer",
        boxSizing: "border-box",
        overflow: "hidden",
        outline: "none",
    });
    const colorSchemeSelect = makeStyledSelect(
        STRUCTURAL_COLOR_OPTIONS,
        typeof params.color_scheme === "string" ? params.color_scheme : "",
        (value) => {
            customColorInput.style.display = value === "uniform" ? "inline-block" : "none";
        },
    );
    colorSchemeSelect.setAttribute(`data-molsysviewer-${options.dataPrefix}-color-scheme`, options.id);
    customColorInput.style.display = colorSchemeSelect.value === "uniform" ? "inline-block" : "none";
    const colorRight = document.createElement("div");
    Object.assign(colorRight.style, {
        display: "flex",
        alignItems: "center",
        gap: "6px",
    });
    colorRight.appendChild(customColorInput);
    colorRight.appendChild(colorSchemeSelect);

    return {
        representationSelect,
        presetSelect,
        qualitySelect,
        opacityInput,
        opacityValue,
        colorSchemeSelect,
        customColorInput,
        representationRow: makeStyleControlRow("Representation", representationSelect),
        presetRow: makeStyleControlRow("Preset", presetSelect),
        qualityRow: makeStyleControlRow("Quality", qualitySelect),
        colorRow: makeStyleControlRow("Color", colorRight),
        opacityRow: makeStyleControlRow("Opacity", opacityWrap),
    };
}
