import fs from "node:fs";

// Where the version comes from when the JS build runs, in the order it is trusted.
//
// `_version.py` is the source in a checkout: versioningit writes it when the Python
// package is built or installed, and it carries the exact `X.Y.Z+N.gSHA` a development
// build should report. But three callers legitimately build the runtime before any Python
// exists — the npm release workflow (tag in hand, no Python at all), `conda-build`'s
// `build.sh` (which exports `RELEASE_VERSION` from `PKG_VERSION` and builds the bundle
// before `pip install`), and CI_e2e. `sync-python-version.mjs` already knew this and fell
// back to the environment; `build-runtime.mjs` did not, and threw `ENOENT`. That single
// difference is why 0.20.1, 0.22.0 and 0.23.0 never reached npm and why the next conda
// build would have failed too (uibcdf/molsysviewer#88).
//
// Both scripts now resolve through here, so the two cannot drift again.

const RELEASE_PATTERN = /^\d+\.\d+\.\d+(?:[A-Za-z0-9._+-]*)?$/;

function readPythonVersion(filePath) {
  const text = fs.readFileSync(filePath, "utf8");
  const match = text.match(/__version__\s*=\s*["']([^"']+)["']/);
  if (!match) {
    throw new Error(`Unable to find __version__ in ${filePath}`);
  }
  return match[1];
}

/**
 * @param {object} options
 * @param {string} options.versionFile      path to `molsysviewer/_version.py`
 * @param {string} [options.fallbackVersion] last resort, normally `package.json`'s version
 * @param {object} [options.env]            defaults to `process.env`
 * @param {(message: string) => void} [options.warn]
 * @returns {{version: string, source: "version-file" | "environment" | "fallback"}}
 */
export function resolveBuildVersion({
  versionFile,
  fallbackVersion,
  env = process.env,
  warn = console.warn,
} = {}) {
  if (fs.existsSync(versionFile)) {
    return { version: readPythonVersion(versionFile), source: "version-file" };
  }

  const candidate =
    env.RELEASE_VERSION || env.GITHUB_REF_NAME || env.GIT_REF_NAME;
  if (candidate && RELEASE_PATTERN.test(candidate.replace(/^v/, ""))) {
    const version = candidate.replace(/^v/, "");
    warn(
      `[resolve-version] ${versionFile} not found. Using ${version} from environment.`,
    );
    return { version, source: "environment" };
  }

  // Reached only outside a release: no Python and no tag. Reusing the manifest's version
  // keeps a developer's `npm run build:runtime` working, and it is the one path that can
  // report a version older than the code, so it says so out loud.
  const version = fallbackVersion || "0.0.0";
  warn(
    `[resolve-version] ${versionFile} not found and no release version is available. Reusing ${version}.`,
  );
  return { version, source: "fallback" };
}
