// Validate c8's actual reports before they can be accepted or uploaded (#290).
import assert from "node:assert/strict";
import { readFileSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const jsRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = realpathSync(resolve(jsRoot, "src"));
const reportRoot = resolve(jsRoot, process.argv[2] || "coverage-js");

try {
    const summary = JSON.parse(readFileSync(resolve(reportRoot, "coverage-summary.json"), "utf8"));
    const lcov = readFileSync(resolve(reportRoot, "lcov.info"), "utf8");
    const entries = Object.entries(summary).filter(([name]) => name !== "total");
    assert(entries.length > 0, "no production source records");
    const measured = new Map();
    for (const [name, counters] of entries) {
        const source = realpathSync(name);
        const inside = relative(sourceRoot, source);
        assert(inside && !inside.startsWith(`..${sep}`) && !isAbsolute(inside) && source.endsWith(".ts"),
            `coverage contains a non-production source: ${name}`);
        assert(!measured.has(source), `duplicate source: ${name}`);
        measured.set(source, counters);
    }
    const seen = new Set();
    for (const record of lcov.split("end_of_record").filter(value => value.trim())) {
        const sourceName = /^SF:(.+)$/m.exec(record)?.[1]?.trim();
        assert(sourceName, "LCOV record has no source");
        const source = realpathSync(resolve(jsRoot, sourceName));
        assert(measured.has(source) && !seen.has(source), `unexpected LCOV source: ${sourceName}`);
        seen.add(source);
        const counters = measured.get(source);
        const count = key => {
            const value = new RegExp(`^${key}:(\\d+)\\s*$`, "m").exec(record);
            assert(value, `LCOV has no ${key}: ${sourceName}`);
            return Number(value[1]);
        };
        const lines = [...record.matchAll(/^DA:(\d+),(\d+)(?:,[^\r\n]*)?\s*$/gm)];
        assert.equal(lines.length, count("LF"), `missing LCOV lines: ${sourceName}`);
        assert.equal(lines.filter(line => Number(line[2]) > 0).length, count("LH"),
            `incorrect LCOV hits: ${sourceName}`);
        for (const [key, actual] of [["LF", counters.lines.total], ["LH", counters.lines.covered],
            ["FNF", counters.functions.total], ["FNH", counters.functions.covered]]) {
            assert.equal(count(key), actual, `LCOV/summary disagreement for ${key}: ${sourceName}`);
        }
    }
    assert.equal(seen.size, measured.size, "LCOV is empty or missing production sources");
    // This small production module has real function calls in the complete unit
    // index. Requiring measured functions rejects c8's false all-lines-hit report
    // when source-map URLs are filtered before function ranges are attributed.
    const anchor = measured.get(realpathSync(resolve(sourceRoot, "ui/local-ui-model.ts")));
    assert(anchor?.lines.covered > 0 && anchor?.functions.covered > 0,
        "no executed lines/functions for src/ui/local-ui-model.ts");
    const totals = [...measured.values()].reduce((sum, value) => ({
        lines: sum.lines + value.lines.total,
        covered: sum.covered + value.lines.covered,
        functions: sum.functions + value.functions.covered,
    }), { lines: 0, covered: 0, functions: 0 });
    console.log(`JS source coverage: ${seen.size} files; ${totals.covered}/${totals.lines} lines; ${totals.functions} executed functions`);
} catch (error) {
    console.error(`Invalid JavaScript source coverage: ${error.message}`);
    process.exitCode = 1;
}
