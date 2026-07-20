import assert from "node:assert";
import test from "node:test";

import { TrajectoryPlotOverlay } from "../../src/ui/trajectory-plot-overlay";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public children: FakeElement[] = [];
    public textContent = "";
    public parentElement: FakeElement | null = null;
    public readonly attributes: Record<string, string> = {};
    public readonly tag: string;
    private listeners: Record<string, ((e: any) => void)[]> = {};

    constructor(tag = "div") { this.tag = tag; }

    setAttribute(name: string, value: string) { this.attributes[name] = value; }
    appendChild(child: FakeElement) { child.parentElement = this; this.children.push(child); return child; }
    replaceChildren() { for (const c of this.children) c.parentElement = null; this.children = []; }
    addEventListener(type: string, cb: (e: any) => void) { (this.listeners[type] ||= []).push(cb); }
    getBoundingClientRect() { return { left: 0, top: 0, width: 440, height: 168 }; }
    remove() {
        if (!this.parentElement) return;
        const i = this.parentElement.children.indexOf(this);
        if (i >= 0) this.parentElement.children.splice(i, 1);
        this.parentElement = null;
    }
    dispatch(type: string, e: any) { for (const cb of this.listeners[type] || []) cb(e); }

    /** Depth-first search for the first descendant tagged `tag`. */
    find(tag: string): FakeElement | undefined {
        for (const c of this.children) {
            if (c.tag === tag) return c;
            const nested = c.find(tag);
            if (nested) return nested;
        }
        return undefined;
    }
    findAll(tag: string, acc: FakeElement[] = []): FakeElement[] {
        for (const c of this.children) {
            if (c.tag === tag) acc.push(c);
            c.findAll(tag, acc);
        }
        return acc;
    }
}

function withFakeDom<T>(run: () => T): T {
    const previous = (globalThis as any).document;
    (globalThis as any).document = {
        createElement: (tag: string) => new FakeElement(tag),
        createElementNS: (_ns: string, tag: string) => new FakeElement(tag),
    };
    try {
        return run();
    } finally {
        (globalThis as any).document = previous;
    }
}

test("TrajectoryPlotOverlay stays hidden without series data", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});

        assert.strictEqual(host.children.length, 0);
        overlay.set({ visible: false });
        assert.strictEqual(host.children.length, 0);
        overlay.set({ visible: true, series: [] });
        assert.strictEqual(host.children.length, 0);
    });
});

test("TrajectoryPlotOverlay renders series and moves the playhead", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});

        overlay.set({
            visible: true,
            n_frames: 5,
            series: [{ label: "rmsd", values: [0, 1, 2, 3, 4], color: 0xff0000 }],
            events: [{ frame: 2 }],
        });

        assert.strictEqual(host.children.length, 1);
        const card = host.children[0];
        const svg = card.find("svg");
        assert.ok(svg, "an svg is rendered");
        assert.ok(svg!.find("polyline"), "the series polyline is rendered");

        // Playhead is the styled vertical line; move it and check it tracks the frame.
        overlay.setFrame(0);
        const lines = svg!.findAll("line");
        const playhead = lines.find((l) => l.attributes["stroke"] === "#ffffff");
        assert.ok(playhead, "playhead line exists");
        const xAt0 = playhead!.attributes["x1"];
        overlay.setFrame(4);
        assert.notStrictEqual(playhead!.attributes["x1"], xAt0, "playhead x moves with the frame");
    });
});

test("TrajectoryPlotOverlay seeks to the clicked frame", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const seeks: number[] = [];
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, (f) => seeks.push(f));

        overlay.set({ visible: true, n_frames: 5, series: [{ label: "s", values: [0, 1, 2, 3, 4] }] });
        const card = host.children[0];
        const svg = card.find("svg")!;

        // Middle of the plot area (x≈234 with left margin 40, width 398) → frame 2 of 0..4.
        svg.dispatch("click", { clientX: 234, clientY: 80 });
        assert.deepStrictEqual(seeks, [2]);
    });
});

test("TrajectoryPlotOverlay handles multiple plot cards simultaneously", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});

        overlay.set({ tag: "e2e", visible: true, n_frames: 5, series: [{ label: "e2e", values: [1, 2, 3, 4, 5] }] });
        overlay.set({ tag: "rg", visible: true, n_frames: 5, series: [{ label: "rg", values: [0.5, 0.6, 0.7, 0.8, 0.9] }] });

        assert.strictEqual(host.children.length, 2, "two plot cards are open");

        overlay.setFrame(3);
        const card1Svg = host.children[0].find("svg")!;
        const card2Svg = host.children[1].find("svg")!;
        assert.ok(card1Svg.find("polyline"));
        assert.ok(card2Svg.find("polyline"));

        // Hide one card
        overlay.hide("e2e");
        assert.strictEqual(host.children.length, 1);

        // Hide all cards
        overlay.hide();
        assert.strictEqual(host.children.length, 0);
    });
});

test("TrajectoryPlotOverlay hides on clear", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
        overlay.set({ visible: true, n_frames: 3, series: [{ label: "s", values: [0, 1, 2] }] });
        assert.strictEqual(host.children.length, 1);
        overlay.hide();
        assert.strictEqual(host.children.length, 0);
    });
});
