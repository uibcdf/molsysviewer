export function makeTrajectoryPluginMock() {
    return {
        managers: {
            animation: {
                isAnimating: false,
                stop() {
                    return;
                },
            },
        },
        state: {
            data: {
                selectQ() {
                    return [];
                },
            },
        },
    };
}

export function withWarnCapture<T>(fn: (warnings: string[]) => Promise<T> | T): Promise<T> | T {
    const originalWarn = console.warn;
    const warnings: string[] = [];
    console.warn = (...args: any[]) => {
        warnings.push(args.map(String).join(" "));
    };
    const finalize = () => {
        console.warn = originalWarn;
    };
    try {
        const out = fn(warnings);
        if (out && typeof (out as Promise<T>).then === "function") {
            return (out as Promise<T>).finally(finalize);
        }
        finalize();
        return out;
    } catch (err) {
        finalize();
        throw err;
    }
}
