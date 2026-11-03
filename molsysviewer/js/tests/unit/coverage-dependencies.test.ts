import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";

test("coverage dependencies preserve real include/exclude, negation and async traversal", async () => {
    // Resolve the real installed tooling instead of bundling a substitute matcher.
    const TestExclude = createRequire(import.meta.url)("test-exclude");
    const directory = mkdtempSync(join(tmpdir(), "msv-coverage-"));
    try {
        for (const name of ["src/keep.js", "src/skip/drop.js", "src/skip/keep.js", "src/other.ts", "tests/test.js"]) {
            const path = join(directory, name);
            mkdirSync(dirname(path), { recursive: true });
            writeFileSync(path, "export const value = 1;\n");
        }
        const selector = new TestExclude({
            cwd: directory,
            include: ["src/**/*.js"],
            exclude: ["**/skip/**", "!**/skip/keep.js"],
            extension: [".js"],
        });
        const expected = ["src/keep.js", "src/skip/keep.js"];
        assert.deepEqual(selector.globSync().sort(), expected);
        assert.deepEqual((await selector.glob()).sort(), expected);
        assert.equal(selector.shouldInstrument(join(directory, "src/skip/drop.js")), false);
        assert.equal(selector.shouldInstrument(join(directory, "src/skip/keep.js")), true);
        assert.equal(selector.shouldInstrument(join(directory, "src/other.ts")), false);
    } finally {
        rmSync(directory, { recursive: true, force: true });
    }
});
