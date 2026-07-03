import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const jsDir = path.resolve(__dirname, "..");
const pythonVersionFile = path.resolve(jsDir, "..", "_version.py");
const packageJsonFile = path.resolve(jsDir, "package.json");

function readPythonVersion(filePath) {
  const text = fs.readFileSync(filePath, "utf8");
  const match = text.match(/__version__\s*=\s*["']([^"']+)["']/);
  if (!match) {
    throw new Error(`Unable to find __version__ in ${filePath}`);
  }
  return match[1];
}

function pythonToNpmVersion(pyVersion) {
  // versioningit produces PEP440-ish local version `X.Y.Z+distance.g<sha>[.dirty]`.
  // For NPM, keep `version` as the base `X.Y.Z` to avoid churn, and store the
  // full git-derived string as metadata.
  return pyVersion.split("+", 1)[0];
}

let pyVersion = null;
const pkg = JSON.parse(fs.readFileSync(packageJsonFile, "utf8"));
if (fs.existsSync(pythonVersionFile)) {
  pyVersion = readPythonVersion(pythonVersionFile);
} else {
  const envVersion =
    process.env.RELEASE_VERSION ||
    process.env.GITHUB_REF_NAME ||
    process.env.GIT_REF_NAME;
  if (envVersion && /^\d+\.\d+\.\d+(?:[A-Za-z0-9._+-]*)?$/.test(envVersion.replace(/^v/, ""))) {
    pyVersion = envVersion.replace(/^v/, "");
    console.warn(
      `[sync-python-version] _version.py not found. Using ${pyVersion} from environment.`
    );
  } else {
    pyVersion = pkg.version || pkg.pythonVersion || "0.0.0";
    console.warn(
      `[sync-python-version] _version.py not found and no release version is available. Reusing ${pyVersion}.`
    );
  }
}
const npmVersion = pythonToNpmVersion(pyVersion);

pkg.version = npmVersion;
pkg.pythonVersion = pyVersion;
fs.writeFileSync(packageJsonFile, JSON.stringify(pkg, null, 2) + "\n", "utf8");

console.log(`[sync-python-version] ${pkg.name}: version=${npmVersion} (python=${pyVersion})`);
