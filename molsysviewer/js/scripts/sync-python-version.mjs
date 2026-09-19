import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { resolveBuildVersion } from "./resolve-version.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const jsDir = path.resolve(__dirname, "..");
const pythonVersionFile = path.resolve(jsDir, "..", "_version.py");
const packageJsonFile = path.resolve(jsDir, "package.json");

function pythonToNpmVersion(pyVersion) {
  // versioningit produces PEP440-ish local version `X.Y.Z+distance.g<sha>[.dirty]`.
  // For NPM, keep `version` as the base `X.Y.Z` to avoid churn, and store the
  // full git-derived string as metadata.
  return pyVersion.split("+", 1)[0];
}

const pkg = JSON.parse(fs.readFileSync(packageJsonFile, "utf8"));
const { version: pyVersion } = resolveBuildVersion({
  versionFile: pythonVersionFile,
  fallbackVersion: pkg.version || pkg.pythonVersion,
});

const npmVersion = pythonToNpmVersion(pyVersion);

pkg.version = npmVersion;
pkg.pythonVersion = pyVersion;
fs.writeFileSync(packageJsonFile, JSON.stringify(pkg, null, 2) + "\n", "utf8");

console.log(`[sync-python-version] ${pkg.name}: version=${npmVersion} (python=${pyVersion})`);
