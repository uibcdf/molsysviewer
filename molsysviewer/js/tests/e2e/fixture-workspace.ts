import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

/** Dispose only this operation's scratch directory, including failed fixtures. */
export async function withFixtureWorkspace<T>(name: string, operation: (directory: string) => Promise<T>): Promise<T> {
    const directory = await mkdtemp(join(tmpdir(), `msv-e2e-${name}-`));
    try {
        return await operation(directory);
    } finally {
        await rm(directory, { recursive: true, force: true });
    }
}

/** Child caches and Python tempfile roots stay inside the owning workspace. */
export function fixtureEnvironment(directory: string): NodeJS.ProcessEnv {
    return { ...process.env, TMPDIR: directory, TMP: directory, TEMP: directory };
}
