import { Loci } from "molstar/lib/mol-model/loci";
import { StructureElement } from "molstar/lib/mol-model/structure";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";

export type MeasurementToolAction = "distance" | "angle" | "dihedral";

type Notify = (msg: any) => void;

type MeasurementToolStatePayload = {
    event: "interaction_tool_state";
    action: MeasurementToolAction | null;
    status: "started" | "progress" | "completed" | "cancelled";
    required_picks: number;
    picked_count: number;
    remaining_picks: number;
    picks_atom_indices: number[][];
};

type MeasurementCreatedPayload = {
    event: "interaction_measurement_created";
    action: MeasurementToolAction;
    picked_count: number;
    picks_atom_indices: number[][];
};

function lociToAtomIndices(loci: StructureElement.Loci): number[] {
    const atomIndices: number[] = [];
    const seen = new Set<number>();
    for (const element of loci.elements) {
        const size = OrderedSet.size(element.indices);
        for (let i = 0; i < size; i++) {
            const unitIndex = OrderedSet.getAt(element.indices, i);
            const atomIndex = element.unit.elements[unitIndex];
            if (!seen.has(atomIndex)) {
                seen.add(atomIndex);
                atomIndices.push(atomIndex);
            }
        }
    }
    return atomIndices;
}

function normalizeToElementLoci(rawLoci: any): StructureElement.Loci | null {
    if (StructureElement.Loci.is(rawLoci) && !Loci.isEmpty(rawLoci)) {
        return rawLoci;
    }
    const normalized = Loci.normalize(rawLoci, "element", true);
    return StructureElement.Loci.is(normalized) && !Loci.isEmpty(normalized) ? normalized : null;
}

function requiredPicks(action: MeasurementToolAction): number {
    switch (action) {
        case "distance": return 2;
        case "angle": return 3;
        case "dihedral": return 4;
    }
}

export class MeasurementToolController {
    private activeAction: MeasurementToolAction | null = null;
    private picks: StructureElement.Loci[] = [];
    private previousGranularity: any = null;
    private readonly keydownHandler: (event: KeyboardEvent) => void;

    constructor(private readonly plugin: any, private readonly notify?: Notify) {
        this.keydownHandler = (event: KeyboardEvent) => {
            if (event.key !== "Escape") return;
            if (!this.activeAction) return;
            this.cancel();
        };
        if (typeof window !== "undefined") {
            window.addEventListener("keydown", this.keydownHandler, true);
        }
    }

    dispose(): void {
        this.cancel(false);
        if (typeof window !== "undefined") {
            window.removeEventListener("keydown", this.keydownHandler, true);
        }
    }

    start(action: MeasurementToolAction, rawLoci: any): void {
        const loci = normalizeToElementLoci(rawLoci);
        if (!loci) return;
        if (this.activeAction) this.cancel(false);
        this.previousGranularity = this.plugin?.managers?.interactivity?.props?.granularity ?? null;
        this.plugin?.managers?.interactivity?.setProps?.({ granularity: "element" });
        this.activeAction = action;
        this.picks = [loci];
        void this.plugin?.managers?.structure?.measurement?.addOrderLabels?.(this.picks);
        this.emitState("started", action);
    }

    handlePrimaryClick(rawLoci: any): void {
        if (!this.activeAction) return;
        const loci = normalizeToElementLoci(rawLoci);
        if (!loci) return;
        this.picks = [...this.picks, loci];
        void this.plugin?.managers?.structure?.measurement?.addOrderLabels?.(this.picks);
        const action = this.activeAction;
        const needed = requiredPicks(action);
        if (this.picks.length < needed) {
            this.emitState("progress", action);
            return;
        }
        void this.complete(action);
    }

    cancel(notify = true): void {
        if (!this.activeAction) return;
        const action = this.activeAction;
        void this.plugin?.managers?.structure?.measurement?.addOrderLabels?.([]);
        this.restoreGranularity();
        this.activeAction = null;
        this.picks = [];
        if (notify) {
            this.notify?.({
                event: "interaction_tool_state",
                action,
                status: "cancelled",
                required_picks: requiredPicks(action),
                picked_count: 0,
                remaining_picks: requiredPicks(action),
                picks_atom_indices: [],
            } satisfies MeasurementToolStatePayload);
        }
    }

    private async complete(action: MeasurementToolAction): Promise<void> {
        const picks = [...this.picks];
        const measurement = this.plugin?.managers?.structure?.measurement;
        if (action === "distance") {
            await measurement?.addDistance?.(picks[0], picks[1]);
        } else if (action === "angle") {
            await measurement?.addAngle?.(picks[0], picks[1], picks[2]);
        } else {
            await measurement?.addDihedral?.(picks[0], picks[1], picks[2], picks[3]);
        }
        await measurement?.addOrderLabels?.([]);
        this.notify?.({
            event: "interaction_measurement_created",
            action,
            picked_count: picks.length,
            picks_atom_indices: picks.map((loci) => lociToAtomIndices(loci)),
        } satisfies MeasurementCreatedPayload);
        this.notify?.({
            event: "interaction_tool_state",
            action,
            status: "completed",
            required_picks: requiredPicks(action),
            picked_count: picks.length,
            remaining_picks: 0,
            picks_atom_indices: picks.map((loci) => lociToAtomIndices(loci)),
        } satisfies MeasurementToolStatePayload);
        this.restoreGranularity();
        this.activeAction = null;
        this.picks = [];
    }

    private emitState(status: "started" | "progress" | "completed", action: MeasurementToolAction): void {
        const required = requiredPicks(action);
        this.notify?.({
            event: "interaction_tool_state",
            action,
            status,
            required_picks: required,
            picked_count: this.picks.length,
            remaining_picks: Math.max(0, required - this.picks.length),
            picks_atom_indices: this.picks.map((loci) => lociToAtomIndices(loci)),
        } satisfies MeasurementToolStatePayload);
    }

    private restoreGranularity(): void {
        if (this.previousGranularity !== null && this.previousGranularity !== undefined) {
            this.plugin?.managers?.interactivity?.setProps?.({ granularity: this.previousGranularity });
        }
        this.previousGranularity = null;
    }
}
