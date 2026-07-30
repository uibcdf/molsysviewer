export const formatArg = (v: any) => {
    if (v instanceof Error) return v.stack || v.message || String(v);
    if (typeof v === "object") {
        try {
            return JSON.stringify(v);
        } catch {
            return String(v);
        }
    }
    return String(v);
};

export const createLogger = (
    model: any,
    debug: boolean,
    send?: (message: Record<string, unknown>) => void,
) => {
    // Route js_log through the same seam as every other browser->Python message
    // (R1). Falls back to a raw model.send only if no sender is supplied.
    const emit = send ?? ((message: Record<string, unknown>) => model.send(message));
    const sendLog = (level: "info" | "warn" | "error" | "log", ...args: any[]) => {
        if (!debug) return;
        try {
            emit({
                event: "js_log",
                level,
                message: args.map(formatArg).join(" "),
            });
        } catch {
            /* no-op */
        }
    };

    if (debug) {
        ["error", "warn"].forEach(level => {
            const orig = (console as any)[level] as ((...xs: any[]) => void) | undefined;
            (console as any)[level] = (...args: any[]) => {
                if (orig) {
                    try {
                        orig.apply(console, args);
                    } catch {
                        /* ignore */
                    }
                }
                sendLog(level as any, ...args);
            };
        });
    }

    return sendLog;
};
