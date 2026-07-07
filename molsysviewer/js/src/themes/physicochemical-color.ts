import { Color } from "molstar/lib/mol-util/color";
import { Location } from "molstar/lib/mol-model/location";
import { StructureElement, Unit, Bond } from "molstar/lib/mol-model/structure";
import { ColorTheme } from "molstar/lib/mol-theme/color";
import { ThemeDataContext } from "molstar/lib/mol-theme/theme";
import { ParamDefinition as PD } from "molstar/lib/mol-util/param-definition";

export const ResidueToClass: Record<string, string> = {
    // Three letter codes
    'GLY': 'aliphatic', 'ALA': 'aliphatic', 'VAL': 'aliphatic', 'LEU': 'aliphatic', 'ILE': 'aliphatic', 'PRO': 'aliphatic',
    'PHE': 'aromatic', 'TYR': 'aromatic', 'TRP': 'aromatic',
    'ASP': 'acidic', 'GLU': 'acidic',
    'LYS': 'basic', 'ARG': 'basic', 'HIS': 'basic',
    'SER': 'hydroxylic', 'THR': 'hydroxylic',
    'CYS': 'sulfur-containing', 'MET': 'sulfur-containing',
    'ASN': 'amidic', 'GLN': 'amidic',
    // One letter codes
    'G': 'aliphatic', 'A': 'aliphatic', 'V': 'aliphatic', 'L': 'aliphatic', 'I': 'aliphatic', 'P': 'aliphatic',
    'F': 'aromatic', 'Y': 'aromatic', 'W': 'aromatic',
    'D': 'acidic', 'E': 'acidic',
    'K': 'basic', 'R': 'basic', 'H': 'basic',
    'S': 'hydroxylic', 'T': 'hydroxylic',
    'C': 'sulfur-containing', 'M': 'sulfur-containing',
    'N': 'amidic', 'Q': 'amidic'
};

export const PhysicochemicalColorsHex: Record<string, string> = {
    aliphatic: "#ef4444",
    aromatic: "#10b981",
    acidic: "#f59e0b",
    basic: "#0ea5e9",
    hydroxylic: "#ec4899",
    'sulfur-containing': "#eab308",
    amidic: "#2563eb"
};

export const PhysicochemicalColorsInt: Record<string, number> = {
    aliphatic: 0xef4444,
    aromatic: 0x10b981,
    acidic: 0xf59e0b,
    basic: 0x0ea5e9,
    hydroxylic: 0xec4899,
    'sulfur-containing': 0xeab308,
    amidic: 0x2563eb
};

const DEFAULT_COLOR = Color(0xaaaaaa);

export const MsvPhysicochemicalColorThemeName = "msv-physicochemical" as const;

function getAtomicCompId(unit: Unit.Atomic, element: any) {
    return unit.model.atomicHierarchy.atoms.label_comp_id.value(element);
}

function getCoarseCompId(unit: any, element: any) {
    const seqIdBegin = unit.coarseElements.seq_id_begin.value(element);
    const seqIdEnd = unit.coarseElements.seq_id_end.value(element);
    if (seqIdBegin === seqIdEnd) {
        const entityKey = unit.coarseElements.entityKey[element];
        const seq = unit.model.sequence.byEntityKey[entityKey].sequence;
        return seq.compId.value(seqIdBegin - 1);
    }
    return undefined;
}

function getPhysicochemicalColor(compId: string): Color {
    const upper = compId.toUpperCase();
    const cls = ResidueToClass[upper];
    if (cls && PhysicochemicalColorsInt[cls] !== undefined) {
        return Color(PhysicochemicalColorsInt[cls]);
    }
    return DEFAULT_COLOR;
}

function factory(_ctx: ThemeDataContext, _props: {}): ColorTheme<{}, "groupInstance"> {
    function color(location: Location): Color {
        if (StructureElement.Location.is(location)) {
            if (Unit.isAtomic(location.unit)) {
                const compId = getAtomicCompId(location.unit, location.element);
                return getPhysicochemicalColor(compId);
            } else {
                const compId = getCoarseCompId(location.unit, location.element);
                if (compId) return getPhysicochemicalColor(compId);
            }
        } else if (Bond.isLocation(location)) {
            if (Unit.isAtomic(location.aUnit)) {
                const compId = getAtomicCompId(location.aUnit, location.aUnit.elements[location.aIndex]);
                return getPhysicochemicalColor(compId);
            } else {
                const compId = getCoarseCompId(location.aUnit, location.aUnit.elements[location.aIndex]);
                if (compId) return getPhysicochemicalColor(compId);
            }
        }
        return DEFAULT_COLOR;
    }

    return {
        factory,
        granularity: "groupInstance",
        color,
        props: {},
    };
}

export const MsvPhysicochemicalColorThemeProvider: ColorTheme.Provider<{}, typeof MsvPhysicochemicalColorThemeName> = {
    name: MsvPhysicochemicalColorThemeName,
    label: "MSV Physicochemical Class",
    category: ColorTheme.Category.Residue,
    factory,
    getParams: () => ({} as PD.Params),
    defaultValues: {},
    isApplicable: (ctx: ThemeDataContext) => !!ctx.structure,
};
