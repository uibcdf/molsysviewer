import type { NetworkLinkOptions } from "../../shapes";
import { readBoxVectors } from "../../plugin/box-vectors";
import type { LoadedStructure } from "../../plugin/structure";
import { isBoxDisplayProjection, type BoxDisplayMetadata, type BoxDisplayProjection } from "../../messages/box-display";

type Definition = { options: NetworkLinkOptions; metadata: BoxDisplayMetadata };
type Context = {
    getLoaded(): LoadedStructure | undefined;
    getFrame(): number;
    isFollower?(): boolean;
    render(options: NetworkLinkOptions, previous?: string): Promise<string | undefined>;
    remove(ref: string): Promise<void>;
    register(ref: string): void;
    failure(error: unknown): void;
};

/** One active cell and refresh owner; no coordinate arrays or per-frame meshes. */
export class BoxDisplayHandler {
    private definition?: Definition;
    private ref?: string;
    private desiredFrame = 0;
    private observedFrame = 0;
    private observedLoaded?: LoadedStructure;
    private revision = 0;
    private appliedRevision = -1;
    private renderedFrame?: number;
    private refresh?: Promise<void>;
    private failed = false;
    private disposed = false;

    constructor(private readonly context: Context) {}

    async define(options: NetworkLinkOptions, metadata: BoxDisplayMetadata): Promise<void> {
        if (this.disposed) return;
        if (!Number.isSafeInteger(metadata.definition_revision) || metadata.definition_revision < 0
            || !Number.isSafeInteger(metadata.structure_index) || metadata.structure_index < 0
            || typeof metadata.frame_update !== "boolean") throw new Error("Invalid box-display metadata");
        const previous = this.definition;
        if (previous && metadata.definition_revision < previous.metadata.definition_revision) return;
        if (previous && metadata.frame_update && metadata.definition_revision === previous.metadata.definition_revision) {
            this.onFrame(this.context.getFrame());
            await this.whenSettled();
            return;
        }
        this.observedFrame = this.context.getFrame();
        this.observedLoaded = this.context.getLoaded();
        this.desiredFrame = metadata.frame_update ? this.observedFrame : metadata.structure_index;
        this.definition = { options: { ...options }, metadata: { ...metadata } };
        this.revision++;
        await this.queue();
    }

    onFrame(frame: number, force = false): void {
        const loaded = this.context.getLoaded();
        const replaced = loaded !== this.observedLoaded;
        if (!force && frame === this.observedFrame && loaded === this.observedLoaded) return;
        this.observedFrame = frame;
        this.observedLoaded = loaded;
        if (!this.definition || this.disposed) return;
        // A mirror receives the resolved owner's cell with its frame. It must
        // not infer a competing cell from an older in-flight frame projection.
        if (this.context.isFollower?.() && !force) {
            if (replaced) { this.revision++; void this.queue(); }
            return;
        }
        this.desiredFrame = frame;
        this.revision++;
        void this.queue();
    }

    get projection(): BoxDisplayProjection | undefined {
        return this.definition ? { definition_revision: this.definition.metadata.definition_revision,
            structure_index: this.desiredFrame } : undefined;
    }

    async applyProjection(value: unknown): Promise<void> {
        if (!isBoxDisplayProjection(value) || this.disposed || !this.definition
            || value.definition_revision !== this.definition.metadata.definition_revision) return;
        if (this.desiredFrame !== value.structure_index) {
            this.desiredFrame = value.structure_index;
            this.revision++;
        }
        await this.queue();
    }

    forget(): void {
        this.definition = undefined;
        this.ref = undefined;
        this.renderedFrame = undefined;
        this.failed = false;
        this.revision++;
    }

    dispose(): void { this.disposed = true; this.forget(); }
    whenSettled(): Promise<void> { return this.refresh ?? Promise.resolve(); }
    get structureIndex(): number | undefined { return this.renderedFrame; }

    isFrameReady(frame: number): boolean {
        if (this.disposed) return false;
        if (this.refresh) return false;
        if (!this.definition) return !this.failed;
        return !this.failed && this.appliedRevision === this.revision
            && this.renderedFrame === this.desiredFrame && this.observedFrame === frame
            && this.observedLoaded === this.context.getLoaded();
    }

    private queue(): Promise<void> {
        if (this.refresh) return this.refresh;
        let complete!: () => void;
        this.refresh = new Promise<void>(resolve => { complete = resolve; });
        const pending = this.refresh;
        void this.applyLatest().then(complete, error => {
            this.failed = true;
            try { this.context.failure(error); } catch { /* Diagnostics cannot retain the refresh owner. */ }
            complete();
        });
        return pending;
    }

    private async applyLatest(): Promise<void> {
        try {
            while (this.definition && !this.disposed && this.appliedRevision !== this.revision) {
                const definition = this.definition, revision = this.revision, frame = this.desiredFrame;
                const rows = readBoxVectors(this.context.getLoaded()?.boxVectors, frame);
                let removingObsolete = false;
                try {
                    const pairs: number[][][] = [];
                    if (rows) for (let axis = 0; axis < 3; axis++) {
                        const other = [0, 1, 2].filter(index => index !== axis);
                        for (let bits = 0; bits < 4; bits++) {
                            const start = [0, 1, 2].map(dimension => other.reduce((sum, index, bit) =>
                                sum + ((bits >> bit) & 1) * rows[index][dimension], 0));
                            pairs.push([start, start.map((value, dimension) => value + rows[axis][dimension])]);
                        }
                    }
                    if (!rows) throw new Error("No raw box basis is available for the requested structure");
                    const ref = await this.context.render({ ...definition.options, mode: "coordinates", coordinate_pairs: pairs as any }, this.ref);
                    if (!ref) throw new Error("Box geometry did not produce a representation");
                    if (this.disposed || this.definition !== definition) {
                        removingObsolete = true;
                        // Retain ownership if removal fails. A later explicit
                        // clear can still find this cell; capture stays unready.
                        this.ref = ref;
                        await this.context.remove(ref);
                        if (this.ref === ref) this.ref = undefined;
                        continue;
                    }
                    this.ref = ref;
                    this.context.register(ref);
                    this.renderedFrame = frame;
                    this.appliedRevision = revision;
                    this.failed = false;
                } catch (error) {
                    if (removingObsolete) {
                        if (this.ref) this.context.register(this.ref);
                        throw error;
                    }
                    if (this.definition !== definition || this.disposed) continue;
                    if (this.ref) await this.context.remove(this.ref);
                    this.ref = undefined;
                    this.renderedFrame = undefined;
                    this.appliedRevision = revision;
                    this.failed = true;
                    this.context.failure(error);
                }
            }
        } finally { this.refresh = undefined; }
    }
}
