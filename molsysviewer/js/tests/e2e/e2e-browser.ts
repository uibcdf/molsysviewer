import process from "node:process";
import {
    chromium as playwrightChromium,
    type Browser,
    type BrowserContext,
    type BrowserContextOptions,
    type LaunchOptions,
    type Page,
} from "playwright";

export const E2E_GL_ARGS = [
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
];

export function failOrExplicitlySkip(stage: string, error: unknown): never {
    const detail = error instanceof Error ? error.message : String(error);
    const message = `[E2E infrastructure] ${stage}: ${detail}`;
    if (process.env.E2E_ALLOW_SKIP === "1") {
        console.warn(`${message}\n[E2E infrastructure] Explicit skip allowed by E2E_ALLOW_SKIP=1.`);
        process.exit(0);
    }
    throw new Error(
        `${message}\nFix the browser/WebGL environment, or explicitly opt out with E2E_ALLOW_SKIP=1.`,
    );
}

function launchOptions(options: LaunchOptions = {}): LaunchOptions {
    return {
        ...options,
        headless: options.headless ?? true,
        executablePath: options.executablePath ?? process.env.PW_CHROMIUM_BIN ?? "/usr/bin/google-chrome",
        chromiumSandbox: false,
        args: [...new Set([...(options.args ?? []), ...E2E_GL_ARGS])],
    };
}

class IsolatedE2EBrowser {
    private context: BrowserContext | undefined;

    constructor(private readonly browser: Browser) {}

    async newPage(options: BrowserContextOptions = {}): Promise<Page> {
        if (this.context) throw new Error("Each E2E suite may create only one isolated browser context.");
        this.context = await this.browser.newContext(options);
        const page = await this.context.newPage();
        const webgl2 = process.env.E2E_FORCE_WEBGL_UNAVAILABLE === "1"
            ? false
            : await page.evaluate(() => {
                const canvas = document.createElement("canvas");
                return canvas.getContext("webgl2") !== null;
            });
        if (!webgl2) {
            await this.context.close();
            this.context = undefined;
            failOrExplicitlySkip("WebGL2 is unavailable", "Mol* rendering cannot be validated");
        }
        return page;
    }

    version(): string {
        return this.browser.version();
    }

    async close(): Promise<void> {
        await this.context?.close();
        this.context = undefined;
        // For a connected browser this disconnects only this suite's client;
        // the BrowserServer and its Chromium process remain alive.
        await this.browser.close();
    }
}

async function launch(options: LaunchOptions = {}): Promise<IsolatedE2EBrowser> {
    try {
        const endpoint = process.env.E2E_WS_ENDPOINT;
        if (endpoint) {
            const browser = await playwrightChromium.connect(endpoint);
            return new IsolatedE2EBrowser(browser);
        }
        const browser = await playwrightChromium.launch(launchOptions(options));
        return new IsolatedE2EBrowser(browser);
    } catch (error) {
        failOrExplicitlySkip("Chromium launch failed", error);
    }
}

export const chromium = { launch };
export { launchOptions as e2eLaunchOptions };
