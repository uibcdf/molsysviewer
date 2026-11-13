import { build } from "esbuild";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Auxiliary qualification only. Normal runtime/unit/harness builds retain
// their declared installed input and their separately reviewed cache adapter.
const [entry, provider, output, expectedVersion, format = "cjs", globalName] = process.argv.slice(2);
if (!entry || !provider || !output || !expectedVersion || !["cjs", "iife"].includes(format)) {
  throw new Error("Usage: build-molstar-probe.mjs ENTRY PROVIDER OUTFILE VERSION [cjs|iife] [GLOBAL_NAME]");
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const origin = await fs.realpath(provider);
const metadataBytes = await fs.readFile(path.join(origin, "package.json"));
const metadata = JSON.parse(metadataBytes);
if (metadata.name !== "molstar" || metadata.version !== expectedVersion) {
  throw new Error(`The probe requires molstar ${expectedVersion}, received ${metadata.name} ${metadata.version}.`);
}
const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const owners = new Map();
async function packageOwner(file) {
  let directory = path.dirname(file);
  const visited = [];
  while (!owners.has(directory)) {
    visited.push(directory);
    try {
      const data = JSON.parse(await fs.readFile(path.join(directory, "package.json"), "utf8"));
      owners.set(directory, { root: directory, name: data.name });
      break;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    const parent = path.dirname(directory);
    if (parent === directory) { owners.set(directory, null); break; }
    directory = parent;
  }
  const owner = owners.get(directory);
  for (const item of visited) owners.set(item, owner);
  return owner;
}
const nativeInputs = new Map();
const result = await build({
  entryPoints: [path.resolve(entry)], absWorkingDir: root, outfile: path.resolve(output),
  bundle: true, write: false, metafile: true, format, globalName,
  platform: format === "cjs" ? "node" : "browser",
  alias: { molstar: origin },
  plugins: [{
    name: "qualified-molstar-probe-origin",
    setup(builder) {
      // Node probes live outside node_modules; anchor their browser driver too.
      builder.onResolve({ filter: /^playwright$/ }, () => ({ path: require.resolve("playwright"), external: true }));
      builder.onLoad({ filter: /\.(?:[cm]?js|ts|json)$/ }, async args => {
        const file = await fs.realpath(args.path), owner = await packageOwner(file);
        if (owner?.name !== "molstar") return;
        if (owner.root !== origin) throw new Error(`Native probe selected a different Mol* origin: ${owner.root}`);
        const bytes = await fs.readFile(file);
        nativeInputs.set(file, sha256(bytes));
        return { contents: bytes, loader: file.endsWith(".json") ? "json" : file.endsWith(".ts") ? "ts" : "js",
          resolveDir: path.dirname(file) };
      });
    },
  }],
});
if (!nativeInputs.size) throw new Error("The native probe must actually consume Mol* modules.");
for (const input of Object.keys(result.metafile.inputs)) {
  const file = await fs.realpath(path.resolve(root, input)), owner = await packageOwner(file);
  if (owner?.name !== "molstar") continue;
  if (owner.root !== origin) throw new Error(`Native probe selected a different Mol* origin: ${owner.root}`);
  if (!nativeInputs.has(file)) throw new Error(`Unsupported native probe input type: ${file}`);
}
for (const [file, digest] of nativeInputs) {
  if (sha256(await fs.readFile(file)) !== digest) throw new Error(`Native probe input changed while building: ${file}`);
}
// Publish only after checking the bytes actually handed to esbuild. A failed
// origin check must not leave a seemingly qualified executable behind.
for (const item of result.outputFiles) await fs.writeFile(item.path, item.contents, { flag: "wx" });
await fs.writeFile(output + ".inputs.json", JSON.stringify({
  provider: { name: metadata.name, version: metadata.version, root: origin, package_sha256: sha256(metadataBytes) },
  native_inputs: Object.fromEntries(nativeInputs), metafile: result.metafile,
  notice: "Unmodified native input bytes; no Viewer cache repair. Probe assertions define the receiving scope.",
}, null, 2) + "\n", { flag: "wx" });
