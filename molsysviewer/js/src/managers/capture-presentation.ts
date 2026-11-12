/** A pending capture may retain a coherent scene prefix until its native draw.
 * Incoherent prefixes never wait: their scientific replies must remain runnable.
 * The capture owns its existing deadline and cancellation; this adds no clock.
 */
export class CapturePresentationFence {
    private readonly pending = new Set<Promise<void>>();
    private readonly releases = new Set<() => void>();
    private closed = false;

    retain(capture: Promise<unknown>): () => void {
        if (this.closed) return () => {};
        let resolve!: () => void;
        const presented = new Promise<void>(done => { resolve = done; });
        const release = () => {
            this.pending.delete(presented);
            this.releases.delete(release);
            resolve();
        };
        this.pending.add(presented);
        this.releases.add(release);
        void capture.then(release, release);
        return release;
    }

    async afterSceneMessage(isCoherent: () => boolean): Promise<void> {
        if (this.pending.size === 0 || !isCoherent()) return;
        // Hold only captures already running at this scene prefix. A later
        // request must reach its own prefix rather than prolong this barrier.
        await Promise.all([...this.pending]);
    }

    dispose(): void {
        this.closed = true;
        for (const release of [...this.releases]) release();
    }
}
