import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const reviewedVersion = "5.4.1";
const reviewedDigest = "071245677951027360bad1926107349d3a67a043d142baace1f218b0f9b3fb0a";

/**
 * Compatibility repair for #356, until a qualified Mol* release fixes its
 * private component-name cache. Its object keys otherwise retain BasicData,
 * including every coordinate buffer, after the model and plugin close.
 *
 * Change only that cache's key lifetime. Do not change memoize1 globally,
 * component definitions, coordinates, installed dependencies or caller data.
 * An upstream change requires review rather than an unchecked source rewrite.
 */
export function molstarComponentCachePlugin() {
  return {
    name: "molsysviewer-molstar-component-cache",
    async setup(build) {
      const packagePath = require.resolve("molstar/package.json");
      const metadata = JSON.parse(await readFile(packagePath, "utf8"));
      if (metadata.version !== reviewedVersion) {
        throw new Error(`Review Mol* ${metadata.version} component-cache compatibility before building (#356).`);
      }
      const sourcePath = path.join(path.dirname(packagePath), "lib/mol-model-formats/structure/basic/properties.js");
      build.onLoad({ filter: /structure[\\/]basic[\\/]properties\.js$/ }, async args => {
        if (path.resolve(args.path) !== sourcePath) return;
        const source = await readFile(sourcePath, "utf8");
        if (createHash("sha256").update(source).digest("hex") !== reviewedDigest) {
          throw new Error("Mol* component-cache source differs from the reviewed bytes (#356).");
        }
        const begin = "const getUniqueComponentNames = memoize1((data) => {";
        const end = "    return uniqueNames;\n});";
        if (source.split(begin).length !== 2 || source.split(end).length !== 2) {
          throw new Error("Mol* component-cache repair did not match exactly once (#356).");
        }
        return {
          contents: source.replace(begin, [
            "const uniqueComponentNamesCache = new WeakMap();",
            "const getUniqueComponentNames = (data) => {",
            "    if (uniqueComponentNamesCache.has(data)) return uniqueComponentNamesCache.get(data);",
          ].join("\n")).replace(end, [
            "    uniqueComponentNamesCache.set(data, uniqueNames);",
            "    return uniqueNames;",
            "};",
          ].join("\n")),
          loader: "js",
          resolveDir: path.dirname(sourcePath),
        };
      });
    },
  };
}
