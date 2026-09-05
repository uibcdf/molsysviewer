// Shared Python<->TypeScript action contract for the AnyWidget runtime seam (R1).
// This module and molsysviewer/viewer/runtime_router.py load THE SAME file
// (molsysviewer/runtime_actions.json), so both sides classify every action
// identically by construction. See the manifest `comment` for the full contract.

import manifest from "../../../runtime_actions.json";

export const RUNTIME_ACTIONS_PROTOCOL_VERSION = 1 as const;

export type RuntimeActionCategory = "command" | "event" | "request" | "ack" | "error";

const rawManifest = manifest as {
    protocol_version: number;
    actions: Record<string, string>;
    outbound_requests: string[];
    raw: string[];
    data_plane: string[];
    qt_transport: string[];
    qt_test_actions: string[];
    popup_actions: Record<string, string[]>;
    frontend_authoritative?: string[];
    render_placements: string[];
    endpoint_role_capabilities: Record<string, string[]>;
};

if (rawManifest.protocol_version !== RUNTIME_ACTIONS_PROTOCOL_VERSION) {
    throw new Error(
        `runtime_actions.json protocol_version must be ${RUNTIME_ACTIONS_PROTOCOL_VERSION}`,
    );
}

const VALID: ReadonlySet<string> = new Set(["command", "event", "request", "ack", "error"]);

export const ACTION_CATEGORIES: ReadonlyMap<string, RuntimeActionCategory> = new Map(
    Object.entries(rawManifest.actions).map(([name, category]) => {
        if (!VALID.has(category)) {
            throw new Error(`runtime_actions.json action ${name} has invalid category ${category}`);
        }
        return [name, category as RuntimeActionCategory];
    }),
);

export const OUTBOUND_REQUESTS: ReadonlySet<string> = new Set(rawManifest.outbound_requests);

/**
 * Host<->popup wire actions and the directions each may carry. `sync-op` is
 * bidirectional on purpose — a projection from the host, a command from the
 * popup — which is precisely why direction is declared in the envelope instead
 * of inferred from which window sent it, the defect this vocabulary had.
 */
export const POPUP_ACTIONS: ReadonlyMap<string, ReadonlySet<string>> = new Map(
    Object.entries(rawManifest.popup_actions ?? {}).map(
        ([action, directions]) => [action, new Set(directions)] as const,
    ),
);

/** True when `action` may legitimately travel in `direction` on the popup channel. */
export function popupActionAllows(action: string, direction: string): boolean {
    return POPUP_ACTIONS.get(action)?.has(direction) ?? false;
}
/**
 * Actions the browser performs itself and merely reports to Python.
 *
 * The distinction only becomes visible where there is no Python: a static export
 * can then tell a control that silently cannot work there from one that already
 * did the work before telling anybody.
 */
export const FRONTEND_AUTHORITATIVE: ReadonlySet<string> =
    new Set(rawManifest.frontend_authoritative ?? []);

export const RAW_ACTIONS: ReadonlySet<string> = new Set(rawManifest.raw);
export const DATA_PLANE_ACTIONS: ReadonlySet<string> = new Set(rawManifest.data_plane);

export const RENDER_PLACEMENTS: ReadonlySet<string> = new Set(rawManifest.render_placements);
if (
    RENDER_PLACEMENTS.size !== 2
    || !RENDER_PLACEMENTS.has("client")
    || !RENDER_PLACEMENTS.has("server")
) {
    throw new Error("runtime_actions.json render_placements must be exactly client and server");
}

export const ENDPOINT_ROLE_CAPABILITIES: ReadonlyMap<string, ReadonlySet<string>> = new Map(
    Object.entries(rawManifest.endpoint_role_capabilities).map(([role, capabilities]) => {
        if (role.trim().length === 0 || capabilities.some(item => item.trim().length === 0)) {
            throw new Error(`runtime_actions.json role ${role} has an invalid capability`);
        }
        if (new Set(capabilities).size !== capabilities.length) {
            throw new Error(`runtime_actions.json role ${role} repeats a capability`);
        }
        return [role, new Set(capabilities)] as const;
    }),
);

export const ENDPOINT_CAPABILITIES: ReadonlySet<string> = new Set(
    [...ENDPOINT_ROLE_CAPABILITIES.values()].flatMap(capabilities => [...capabilities]),
);

export function endpointRoleAllowsCapability(role: string, capability: string): boolean {
    return ENDPOINT_ROLE_CAPABILITIES.get(role)?.has(capability) ?? false;
}

// Groups must be pairwise disjoint, matching the Python loader's guarantee.
(() => {
    const groups: ReadonlySet<string>[] = [
        new Set(ACTION_CATEGORIES.keys()),
        OUTBOUND_REQUESTS,
        RAW_ACTIONS,
        DATA_PLANE_ACTIONS,
    ];
    const seen = new Set<string>();
    for (const group of groups) {
        for (const name of group) {
            if (seen.has(name)) {
                throw new Error(`runtime_actions.json action appears in two groups: ${name}`);
            }
            seen.add(name);
        }
    }
})();

/** Manifest category for a browser-originated action, or `undefined` if unknown. */
export function categoryOf(action: string): RuntimeActionCategory | undefined {
    return ACTION_CATEGORIES.get(action);
}
