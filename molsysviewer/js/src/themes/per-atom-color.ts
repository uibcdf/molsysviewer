// src/themes/per-atom-color.ts
//
// A Mol* ColorTheme that paints each atom with a colour looked up from a
// module-level Map populated by the `set_atom_colors` / `clear_atom_colors`
// messages received from Python.

import { Color } from "molstar/lib/mol-util/color";
import { Location } from "molstar/lib/mol-model/location";
import { StructureElement } from "molstar/lib/mol-model/structure";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { ColorTheme } from "molstar/lib/mol-theme/color";
import { ThemeDataContext } from "molstar/lib/mol-theme/theme";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";

// ── Shared mutable state ──────────────────────────────────────────────────────

/** atomIndex (model-level, 0-based) → 0xRRGGBB color integer */
const _perAtomColorMap = new Map<number, number>();

const DEFAULT_COLOR = Color(0xaaaaaa);

export const MsvPerAtomColorThemeName = "msv-per-atom" as const;

// ── Theme factory ─────────────────────────────────────────────────────────────

function factory(_ctx: ThemeDataContext, _props: {}): ColorTheme<{}, "groupInstance"> {
    return {
        factory,
        granularity: "groupInstance",
        color: (location: Location): Color => {
            if (!StructureElement.Location.is(location)) return DEFAULT_COLOR;
            const atomIndex = OrderedSet.getAt(location.unit.elements, location.element);
            const c = _perAtomColorMap.get(atomIndex);
            return c !== undefined ? Color(c) : DEFAULT_COLOR;
        },
        props: {},
    };
}

// ── Provider ──────────────────────────────────────────────────────────────────

export const MsvPerAtomColorThemeProvider: ColorTheme.Provider<{}, typeof MsvPerAtomColorThemeName> = {
    name: MsvPerAtomColorThemeName,
    label: "MSV Per-Atom Color",
    category: ColorTheme.Category.Atom,
    factory,
    getParams: () => ({} as PD.Params),
    defaultValues: {},
    isApplicable: (ctx: ThemeDataContext) => !!ctx.structure,
};

// ── Map mutation helpers ──────────────────────────────────────────────────────

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
