import assert from "node:assert";
import test from "node:test";

import { TrajectoryPlotOverlay } from "../../src/ui/trajectory-plot-overlay";

test("numeric x positions, events and playhead agree for irregular samples", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const sought: number[] = [];
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, frame => sought.push(frame));
        overlay.set({ visible: true, width: 440, n_frames: 4, x: [10, 11, 20, 11],
            series: [{ label: "values", values: [1, 2, 3, 4] }], events: [{ frame: 1 }] });
        const svg = host.find("svg")!;
        const positions = svg.find("polyline")!.attributes.points.split(" ").map(point => Number(point.split(",")[0]));
        assert.ok(Math.abs((positions[1] - positions[0]) / (positions[2] - positions[0]) - 0.1) < 1e-9);
        assert.equal(positions[1], positions[3]);
        const lines = svg.findAll("line");
        assert.equal(Number(lines.find(line => line.attributes["stroke"] === "#f59e0b")!.attributes.x1), positions[1]);
        overlay.setFrame(3);
        assert.equal(Number(lines.find(line => line.attributes["stroke"] === "#ffffff")!.attributes.x1), positions[3]);
        svg.dispatch("click", { clientX: positions[1], preventDefault() {} });
        assert.equal(sought.at(-1), 3, "a repeated x preserves the current frame");
        overlay.setFrame(0);
        svg.dispatch("click", { clientX: positions[1], preventDefault() {} });
        assert.equal(sought.at(-1), 1, "otherwise a tie chooses the earliest matching frame");
        assert.equal(numericText(svg, "x-min").find("tspan")!.textContent, "10");
        assert.equal(numericText(svg, "x-max").find("tspan")!.textContent, "20");
    });
});

test("finite extreme and constant plot values produce finite SVG coordinates", () => {
    withFakeDom(() => {
        for (const values of [[-1e308, 0, 1e308], [1e300, 1e300, 1e300],
            [Number.MIN_VALUE, 2 * Number.MIN_VALUE, 3 * Number.MIN_VALUE]]) {
            const host = new FakeElement();
            const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
            overlay.set({ visible: true, n_frames: 3, x: [-1e308, 0, 1e308],
                series: [{ label: "finite", values }] });
            const points = host.find("polyline")!.attributes.points.split(" ").map(point => point.split(",").map(Number));
            assert.ok(points.flat().every(Number.isFinite));
            assert.ok(points[0][0] < points[1][0] && points[1][0] < points[2][0]);
        }
    });
});

test("tiny signed values and narrow limits remain distinct without changing raw values", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
        const cases = [
            { x: [1.0001, 1.0002, 1.0005], y: [0.0001, 0.0002, 0.0005], limits: ["1.0001", "1.0005"], y0: "1e-4" },
            { x: [1.0001, 1.0002, 1.0005], y: [0.001, 0.002, 0.005], limits: ["1.0001", "1.0005"], y0: "0.001" },
            { x: [-2e-8, 0, 2e-8], y: [-1e-8, 0, 1e-8], limits: ["-2e-8", "2e-8"], y0: "-1e-8" },
            { x: [1, 1 + Number.EPSILON, 1 + 2 * Number.EPSILON], y: [1, 2, 3],
                limits: ["1", "1.0000000000000004"], y0: "1" },
            { x: [999999.9999999999, 1e6, 1e6], y: [1, 2, 3],
                limits: ["999999.9999999999", "1e6"], y0: "1" },
            { x: [0.0009999999999999998, 0.001, 0.001], y: [1, 2, 3],
                limits: ["9.999999999999998e-4", "0.001"], y0: "1" },
        ];
        for (const fixture of cases) {
            const before = structuredClone(fixture);
            overlay.set({ x: fixture.x, series: [{ label: "control", values: fixture.y }] });
            overlay.setFrame(0);
            const svg = host.find("svg")!;
            assert.deepEqual(["x-min", "x-max"].map(name => numericText(svg, name).find("tspan")!.textContent), fixture.limits);
            const readout = numericText(svg, "readout");
            assert.equal(readout.find("tspan")!.textContent, `x: ${fixture.limits[0]} · y: ${fixture.y0}`);
            assert.equal(readout.find("title")!.textContent, `x: ${fixture.x[0]} · y: ${fixture.y[0]}`);
            assert.equal(readout.attributes["aria-label"], readout.find("title")!.textContent);
            assert.equal(readout.attributes.tabindex, "0");
            assert.deepEqual(fixture, before, "formatting must not modify the caller's values");
        }
    });
});

test("adjacent limits near the maximum finite value do not round beyond binary64", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
        const values = [1.7976931348623153e308, 1.7976931348623155e308, Number.MAX_VALUE];
        overlay.set({ x: values, series: [{ label: "extreme", values }] });
        const svg = host.find("svg")!;
        const limits = ["x-min", "x-max"].map(name => numericText(svg, name).find("tspan")!.textContent);
        assert.deepEqual(limits.map(Number), [values[0], values[2]]);
        assert.ok(limits.map(Number).every(Number.isFinite));
    });
});

test("large-offset geometry subtracts represented values before normalization", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
        const values = [1e12 + 0.001, 1e12 + 0.002, 1e12 + 0.003];
        overlay.set({ x: values, series: [{ label: "offset", values }] });
        const svg = host.find("svg")!;
        const points = svg.find("polyline")!.attributes.points.split(" ").map(point => point.split(",").map(Number));
        // These represented binary64 offsets are 8, 16 and 25 times 2^-13.
        const expected = 8 / 17;
        for (const dimension of [0, 1]) {
            const fraction = (points[1][dimension] - points[0][dimension]) / (points[2][dimension] - points[0][dimension]);
            assert.ok(Math.abs(fraction - expected) < 1e-12);
        }
        overlay.setFrame(1);
        const readout = numericText(svg, "readout");
        assert.equal(readout.find("tspan")!.textContent, "x: 1.000000000000002e12 · y: 1.000000000000002e12");
        assert.equal(readout.find("title")!.textContent, "x: 1000000000000.002 · y: 1000000000000.002");
        assert.notEqual(numericText(svg, "x-min").find("tspan")!.textContent, numericText(svg, "x-max").find("tspan")!.textContent);
    });
});

test("rounded readouts in broad ranges retain full raw access for nearby samples and signed zero", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
        const values = [0, 1e12 + 0.001, 1e12 + 0.002];
        overlay.set({ x: values, series: [{ label: "broad", values: [-0, 1e-8, 2e-8] }] });
        const svg = host.find("svg")!;
        const readout = numericText(svg, "readout");
        overlay.setFrame(0);
        assert.equal(readout.find("tspan")!.textContent, "x: 0 · y: 0");
        assert.equal(readout.find("title")!.textContent, "x: 0 · y: -0");
        overlay.setFrame(1);
        assert.equal(readout.find("tspan")!.textContent, "x: 1e12 · y: 1e-8");
        assert.equal(readout.attributes["aria-label"], "x: 1000000000000.001 · y: 1e-8");
        overlay.setFrame(2);
        assert.equal(readout.attributes["aria-label"], "x: 1000000000000.002 · y: 2e-8");
    });
});

function numericText(svg: FakeElement, name: string): FakeElement {
    const result = svg.findAll("text").find(text => text.attributes["data-molsysviewer-plot-value"] === name);
    assert.ok(result, `missing numeric plot text ${name}`);
    return result;
}

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
    replaceChildren(...children: FakeElement[]) {
        for (const c of this.children) c.parentElement = null;
        this.children = [];
        for (const child of children) this.appendChild(child);
    }
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
        assert.strictEqual(host.children.length, 2);
        assert.strictEqual(host.children[0].style.display, "none");
        assert.strictEqual(host.children[1].style.display, "flex");

        // Hide all cards
        overlay.hide();
        assert.ok(host.children.every(card => card.style.display === "none"));
        overlay.set({ cards: [] });
        assert.strictEqual(host.children.length, 0);
    });
});

test("TrajectoryPlotOverlay retains hidden data and clears an empty canonical registry", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new TrajectoryPlotOverlay(host as unknown as HTMLElement, () => {});
        overlay.set({ visible: true, n_frames: 3, series: [{ label: "s", values: [0, 1, 2] }] });
        assert.strictEqual(host.children.length, 1);
        overlay.hide();
        assert.strictEqual(host.children.length, 1);
        assert.strictEqual(host.children[0].style.display, "none");
        overlay.set({ cards: [] });
        assert.strictEqual(host.children.length, 0);
    });
});
