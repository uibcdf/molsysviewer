import assert from "node:assert";
import test from "node:test";

import { MeasurementToolController } from "../../src/managers/measurement-tools";

function makeLoci(atomIndices: number[]): any {
    return {
        kind: "element-loci",
        structure: {},
        elements: [
            {
                unit: { elements: atomIndices },
                indices: atomIndices.map((_, index) => index),
            },
        ],
    };
}

test("MeasurementToolController creates a distance measurement from seeded context pick plus one click", async () => {
    const notifications: any[] = [];
    const calls: string[] = [];
    const plugin: any = {
        managers: {
            interactivity: {
                props: { granularity: "residue" },
                setProps(next: any) {
                    this.props = { ...this.props, ...next };
                    calls.push(`granularity:${next.granularity}`);
                },
            },
            structure: {
                measurement: {
                    async addOrderLabels(locis: any[]) {
                        calls.push(`order:${locis.length}`);
                    },
                    async addDistance(a: any, b: any) {
                        calls.push(`distance:${a.elements[0].unit.elements[0]}-${b.elements[0].unit.elements[0]}`);
                    },
                },
            },
        },
    };

    const controller = new MeasurementToolController(plugin, (msg) => notifications.push(msg));
    controller.start("distance", makeLoci([10]));
    controller.handlePrimaryClick(makeLoci([25]));
    await new Promise((resolve) => setImmediate(resolve));
    controller.dispose();

    assert.deepStrictEqual(calls, [
        "granularity:element",
        "order:1",
        "order:2",
        "distance:10-25",
        "order:0",
        "granularity:residue",
    ]);
    assert.deepStrictEqual(notifications, [
        {
            event: "interaction_tool_state",
            action: "distance",
            status: "started",
            required_picks: 2,
            picked_count: 1,
            remaining_picks: 1,
            picks_atom_indices: [[10]],
        },
        {
            event: "interaction_measurement_created",
            action: "distance",
            picked_count: 2,
            picks_atom_indices: [[10], [25]],
        },
        {
            event: "interaction_tool_state",
            action: "distance",
            status: "completed",
            required_picks: 2,
            picked_count: 2,
            remaining_picks: 0,
            picks_atom_indices: [[10], [25]],
        },
    ]);
});
