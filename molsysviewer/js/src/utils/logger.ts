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

export const createLogger = (model: any, debug: boolean) => {
    const sendLog = (level: "info" | "warn" | "error" | "log", ...args: any[]) => {
        if (!debug) return;
        try {
            model.send({
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
