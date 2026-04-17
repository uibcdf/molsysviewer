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
                },
            },
        },
    };

    const controller = new MeasurementToolController(
        plugin,
        (msg) => notifications.push(msg),
        async ({ action, picks_atom_indices }) => {
            calls.push(`${action}:${picks_atom_indices[0]?.[0]}-${picks_atom_indices[1]?.[0]}`);
            return {
                tag: "measurement_1",
                endpoint_policy: "centroid",
                endpoint_kinds: ["atom", "atom"],
                endpoint_labels: ["atom", "atom"],
                endpoint_atom_indices: [[10], [25]],
            };
        },
    );
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
            endpoint_kinds: ["atom", "atom"],
            endpoint_policy: "centroid",
            endpoint_labels: ["atom", "atom"],
            endpoint_atom_indices: [[10], [25]],
            tag: "measurement_1",
            value: undefined,
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

test("MeasurementToolController cancels active tool state and restores granularity", async () => {
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
                },
            },
        },
    };

    const controller = new MeasurementToolController(plugin, (msg) => notifications.push(msg));
    controller.start("angle", makeLoci([10]));
    controller.cancel();
    await new Promise((resolve) => setImmediate(resolve));
    controller.dispose();

    assert.deepStrictEqual(calls, [
        "granularity:element",
        "order:1",
        "order:0",
        "granularity:residue",
    ]);
    assert.deepStrictEqual(notifications, [
        {
            event: "interaction_tool_state",
            action: "angle",
            status: "started",
            required_picks: 3,
            picked_count: 1,
            remaining_picks: 2,
            picks_atom_indices: [[10]],
        },
        {
            event: "interaction_tool_state",
            action: "angle",
            status: "cancelled",
            required_picks: 3,
            picked_count: 0,
            remaining_picks: 3,
            picks_atom_indices: [],
        },
    ]);
});

test("MeasurementToolController reports centroid endpoint policy for multi-atom picks", async () => {
    const notifications: any[] = [];
    const plugin: any = {
        managers: {
            interactivity: {
                props: { granularity: "residue" },
                setProps(next: any) {
                    this.props = { ...this.props, ...next };
                },
            },
            structure: {
                measurement: {
                    async addOrderLabels() {},
                },
            },
        },
    };

    const controller = new MeasurementToolController(plugin, (msg) => notifications.push(msg));
    controller.start("distance", makeLoci([10, 11]));
    controller.handlePrimaryClick(makeLoci([25]));
    await new Promise((resolve) => setImmediate(resolve));
    controller.dispose();

    assert.deepStrictEqual(notifications[1], {
        event: "interaction_measurement_created",
        action: "distance",
        picked_count: 2,
        picks_atom_indices: [[10, 11], [25]],
        endpoint_kinds: ["centroid", "atom"],
        endpoint_policy: "centroid",
        endpoint_labels: ["centroid", "atom"],
        endpoint_atom_indices: [[], [25]],
        tag: undefined,
        value: undefined,
    });
});
