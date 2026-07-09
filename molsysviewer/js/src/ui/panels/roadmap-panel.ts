import { StudioPanel } from "./types";
import { makeSectionHeader, makeSettingsCard } from "./ui-helpers";

export interface RoadmapConfig {
    /** Section header text. */
    header: string;
    /** Card title. */
    cardTitle: string;
    /** Intro paragraph. */
    description: string;
    /** Bullet list of planned features. */
    items: string[];
}

/**
 * Placeholder subpanel that renders a static "feature roadmap" card.
 *
 * Used for subpanels whose real functionality is not built yet (Whole, Layers).
 * When a subpanel gains real content it graduates to its own dedicated module;
 * this keeps the placeholder out of `GroupPanel` in the meantime.
 */
export class RoadmapPanel implements StudioPanel {
    private host: HTMLElement | null = null;

    constructor(
        readonly key: string,
        private readonly config: RoadmapConfig,
    ) {}

    mount(host: HTMLElement): void {
        this.host = host;
        this.render();
    }

    private render(): void {
        if (!this.host) return;
        this.host.replaceChildren();
        this.host.appendChild(makeSectionHeader(this.config.header));

        const card = makeSettingsCard(this.config.cardTitle);

        const desc = document.createElement("div");
        Object.assign(desc.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            lineHeight: "1.5",
            marginBottom: "8px",
        });
        desc.textContent = this.config.description;
        card.appendChild(desc);

        const list = document.createElement("ul");
        Object.assign(list.style, {
            fontSize: "11px",
            color: "rgba(244,244,245,0.7)",
            lineHeight: "1.6",
            paddingLeft: "16px",
            margin: "0",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });
        for (const itemText of this.config.items) {
            const li = document.createElement("li");
            li.textContent = itemText;
            list.appendChild(li);
        }
        card.appendChild(list);

        this.host.appendChild(card);
    }
}
