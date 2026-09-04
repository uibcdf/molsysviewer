import {
    type ExpectedRemoteIdentity,
    type RemotePacketValidation,
    validateInputPacket,
} from "./remote-protocol";

type EventInitRecord = Record<string, unknown>;

export interface RemoteInputEventFactory {
    mouse(type: string, init: EventInitRecord): Event;
    wheel(type: string, init: EventInitRecord): Event;
    key(type: string, init: EventInitRecord): Event;
}

export interface RemoteInputRatePolicy {
    maxEvents: number;
    intervalMs: number;
    now?: () => number;
}

export type RemoteInputDispatchResult =
    | { status: "accepted"; sequence: number; eventType: string }
    | { status: "rejected"; reason: string; detail: string };

const browserEventFactory: RemoteInputEventFactory = {
    mouse: (type, init) => new MouseEvent(type, init as MouseEventInit),
    wheel: (type, init) => new WheelEvent(type, init as WheelEventInit),
    key: (type, init) => new KeyboardEvent(type, init as KeyboardEventInit),
};

function rejection(result: RemotePacketValidation): RemoteInputDispatchResult {
    if (result.status !== "rejected") {
        throw new Error("accepted remote packet cannot be converted to a rejection");
    }
    return result;
}

function modifiers(payload: Record<string, unknown>) {
    const value = (payload.modifiers ?? {}) as Record<string, boolean>;
    return {
        altKey: value.alt === true,
        ctrlKey: value.ctrl === true,
        metaKey: value.meta === true,
        shiftKey: value.shift === true,
    };
}

/** Dispatch validated remote input through the real Mol* canvas event path. */
export class RemoteInputAdapter {
    private lastSequence = -1;
    private rateWindowStartedAt: number;
    private acceptedInRateWindow = 0;
    private readonly rateNow: () => number;

    constructor(
        private readonly target: HTMLElement,
        private readonly expectedIdentity: ExpectedRemoteIdentity,
        private readonly eventFactory: RemoteInputEventFactory = browserEventFactory,
        private readonly globalTarget: EventTarget = target.ownerDocument?.defaultView ?? target,
        private readonly ratePolicy: RemoteInputRatePolicy = { maxEvents: 240, intervalMs: 1_000 },
    ) {
        if (!Number.isInteger(ratePolicy.maxEvents) || ratePolicy.maxEvents < 1
            || !Number.isFinite(ratePolicy.intervalMs) || ratePolicy.intervalMs <= 0) {
            throw new Error("remote input rate policy must be positive and bounded");
        }
        this.rateNow = ratePolicy.now ?? (() => performance.now());
        this.rateWindowStartedAt = this.rateNow();
    }

    get acceptedSequence(): number {
        return this.lastSequence;
    }

    handle(value: unknown): RemoteInputDispatchResult {
        const validation = validateInputPacket(value, this.expectedIdentity);
        if (validation.status === "rejected") return rejection(validation);
        const packet = validation.packet;
        const sequence = packet.sequence as number;
        if (sequence <= this.lastSequence) {
            return {
                status: "rejected",
                reason: "stale-sequence",
                detail: `Input sequence ${sequence} does not follow ${this.lastSequence}`,
            };
        }
        const now = this.rateNow();
        if (now - this.rateWindowStartedAt >= this.ratePolicy.intervalMs) {
            this.rateWindowStartedAt = now;
            this.acceptedInRateWindow = 0;
        }
        if (this.acceptedInRateWindow >= this.ratePolicy.maxEvents) {
            return {
                status: "rejected",
                reason: "rate-limit",
                detail: `Input exceeds ${this.ratePolicy.maxEvents} events per ${this.ratePolicy.intervalMs} ms`,
            };
        }

        const kind = packet.kind as string;
        const payload = packet.payload as Record<string, unknown>;
        const event = this.buildEvent(kind, payload);
        this.lastSequence = sequence;
        this.acceptedInRateWindow += 1;
        if (kind === "pointer" && payload.phase === "down") this.target.focus();
        const usesGlobalTarget = kind === "key"
            || (kind === "pointer" && payload.phase !== "down");
        (usesGlobalTarget ? this.globalTarget : this.target).dispatchEvent(event);
        return { status: "accepted", sequence, eventType: event.type };
    }

    private buildEvent(kind: string, payload: Record<string, unknown>): Event {
        const common = { bubbles: true, cancelable: true, ...modifiers(payload) };
        if (kind === "key") {
            const type = payload.phase === "down" ? "keydown" : "keyup";
            return this.eventFactory.key(type, {
                ...common,
                code: payload.code,
                repeat: payload.repeat,
            });
        }

        const rect = this.target.getBoundingClientRect();
        const positioned = {
            ...common,
            clientX: rect.left + rect.width * (payload.x as number),
            clientY: rect.top + rect.height * (payload.y as number),
        };
        if (kind === "wheel") {
            return this.eventFactory.wheel("wheel", {
                ...positioned,
                deltaX: payload.deltaX,
                deltaY: payload.deltaY,
                deltaMode: payload.deltaMode,
            });
        }

        // Mol* InputObserver listens for mousedown on its canvas, mousemove/up
        // on window (so drags continue outside the canvas), and keyboard events
        // on window. Keep this adapter on that real path instead of introducing
        // a parallel picking implementation.
        const phaseToType: Record<string, string> = {
            move: "mousemove",
            down: "mousedown",
            up: "mouseup",
            cancel: "mouseup",
        };
        return this.eventFactory.mouse(phaseToType[payload.phase as string], {
            ...positioned,
            button: payload.button,
            buttons: payload.buttons,
        });
    }
}
