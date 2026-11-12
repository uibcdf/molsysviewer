import path from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { molstarComponentCachePlugin } from "./molstar-component-cache.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const targets = {
  unit: {
    entryPoints: [path.join(root, "tests/unit/index.test.ts")],
    platform: "node",
    format: "esm",
    outfile: path.join(root, "tests/unit/dist-index.js"),
    external: ["typescript"],
    sourcemap: true,
  },
  harness: {
    entryPoints: [path.join(root, "tests/e2e/harness.ts")],
    format: "iife",
    globalName: "Harness",
    outfile: path.join(root, "tests/e2e/harness.bundle.js"),
  },
};
const target = targets[process.argv[2]];
if (!target) throw new Error("Select the unit or harness build target.");
await build({ ...target, bundle: true, plugins: [molstarComponentCachePlugin()] });
