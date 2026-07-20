// src/themes/per-atom-color.ts
//
// A Mol* ColorTheme that paints each atom with a colour looked up from a
// module-level Map populated by the `set_atom_colors` / `clear_atom_colors`
// messages received from Python.

import { Color } from "molstar/lib/mol-util/color";
import { Location } from "molstar/lib/mol-model/location";
import { StructureElement, Bond } from "molstar/lib/mol-model/structure";
import { ColorTheme } from "molstar/lib/mol-theme/color";
import { ThemeDataContext } from "molstar/lib/mol-theme/theme";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";
import { MsvPhysicochemicalColorThemeName, MsvPhysicochemicalColorThemeProvider } from "./physicochemical-color";

// ── Shared mutable state ──────────────────────────────────────────────────────

/** atomIndex (model-level, 0-based) → 0xRRGGBB color integer */
const _perAtomColorMap = new Map<number, number>();

const DEFAULT_BASE_THEME = { name: "element-symbol", params: {} };

export const MsvPerAtomColorThemeName = "msv-per-atom" as const;

const MsvPerAtomColorThemeParams = {
    base: PD.Value(DEFAULT_BASE_THEME as { name: string; params?: any }, { isHidden: true }),
};

type MsvPerAtomColorThemeParams = typeof MsvPerAtomColorThemeParams;

function createBaseTheme(ctx: ThemeDataContext, base: { name: string; params?: any } | undefined) {
    const spec = base?.name && base.name !== MsvPerAtomColorThemeName ? base : DEFAULT_BASE_THEME;
    if (spec.name === MsvPhysicochemicalColorThemeName) {
        return MsvPhysicochemicalColorThemeProvider.factory(ctx, {
            ...MsvPhysicochemicalColorThemeProvider.defaultValues,
            ...(spec.params ?? {}),
        });
    }
    const provider = (ColorTheme.BuiltIn as any)[spec.name] as ColorTheme.Provider | undefined;
    const fallback = ColorTheme.BuiltIn["element-symbol"] as ColorTheme.Provider;
    const selected = provider ?? fallback;
    return selected.factory(ctx, {
        ...selected.defaultValues,
        ...(spec.params ?? {}),
    });
}

function baseColor(baseTheme: any, location: Location, isSecondary: boolean): Color {
    if ("color" in baseTheme && typeof baseTheme.color === "function") {
        return baseTheme.color(location, isSecondary);
    }
    return ColorTheme.Empty.color(location, isSecondary);
}

// ── Theme factory ─────────────────────────────────────────────────────────────

function factory(ctx: ThemeDataContext, props: PD.Values<MsvPerAtomColorThemeParams>): ColorTheme<MsvPerAtomColorThemeParams, "groupInstance"> {
    const baseTheme = createBaseTheme(ctx, props.base);

    // `location.element` is already a model-level ElementIndex, so it is used
    // directly. For bonds, the element index is looked up positionally in the
    // unit's element array via `aIndex` (same convention as the sibling
    // physicochemical theme).
    const colorFor = (atomIndex: number, location: Location): Color => {
        const c = _perAtomColorMap.get(atomIndex);
        return c !== undefined ? Color(c) : baseColor(baseTheme, location, false);
    };

    return {
        factory,
        granularity: "groupInstance",
        color: (location: Location): Color => {
            if (StructureElement.Location.is(location)) {
                return colorFor(location.element, location);
            }
            // Bond visuals (ball-and-stick, line, …) are colored from their
            // first atom; without this branch every bond fell back to the base
            // theme, which made per-atom colors invisible on those
            // representations.
            if (Bond.isLocation(location)) {
                return colorFor(location.aUnit.elements[location.aIndex], location);
            }
            return baseColor(baseTheme, location, false);
        },
        props,
    };
}

// ── Provider ──────────────────────────────────────────────────────────────────

export const MsvPerAtomColorThemeProvider: ColorTheme.Provider<MsvPerAtomColorThemeParams, typeof MsvPerAtomColorThemeName> = {
    name: MsvPerAtomColorThemeName,
    label: "MSV Per-Atom Color",
    category: ColorTheme.Category.Atom,
    factory,
    getParams: () => MsvPerAtomColorThemeParams,
    defaultValues: PD.getDefaultValues(MsvPerAtomColorThemeParams),
    isApplicable: (ctx: ThemeDataContext) => !!ctx.structure,
};

// ── Map mutation helpers ──────────────────────────────────────────────────────

export function getPerAtomColor(atomIndex: number): number | undefined {
    return _perAtomColorMap.get(atomIndex);
}

export function setPerAtomColors(atomIndices: number[], colorInts: number[], replace = true): void {
    if (replace) _perAtomColorMap.clear();
    const len = Math.min(atomIndices.length, colorInts.length);
    for (let i = 0; i < len; i++) {
        _perAtomColorMap.set(atomIndices[i], colorInts[i]);
    }
}

export function clearPerAtomColors(): void {
    _perAtomColorMap.clear();
}

export function clearPerAtomColorsFor(atomIndices: number[]): void {
    for (const atomIndex of atomIndices) {
        _perAtomColorMap.delete(atomIndex);
    }
}

export function hasPerAtomColors(): boolean {
    return _perAtomColorMap.size > 0;
}
