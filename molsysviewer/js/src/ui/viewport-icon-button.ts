export const VIEWPORT_ICON_PANEL = `<rect x="2" y="2" width="12" height="12" rx="1.5"/><line x1="5.5" y1="2.5" x2="5.5" y2="13.5"/>`;
export const VIEWPORT_ICON_FULLSCREEN = `<polyline points="2,5 2,2 5,2"/><polyline points="11,2 14,2 14,5"/><polyline points="14,11 14,14 11,14"/><polyline points="5,14 2,14 2,11"/>`;
export const VIEWPORT_ICON_EXIT_FULLSCREEN = `<polyline points="5,2 5,5 2,5"/><polyline points="11,2 11,5 14,5"/><polyline points="14,11 11,11 11,14"/><polyline points="2,11 5,11 5,14"/>`;
export const VIEWPORT_ICON_POPUP = `<line x1="5.5" y1="10.5" x2="11.5" y2="4.5"/><polyline points="8,4 12,4 12,8"/><polyline points="5.5,7 3,7 3,13 9,13 9,10.5"/>`;
export const VIEWPORT_ICON_HELP = `<circle cx="8" cy="8" r="6"/><path d="M6.2,6.5a1.9,1.9,0,0,1,3.8,0c0,1.9-1.9,1.9-1.9,3" stroke-linecap="round" stroke-linejoin="round"/><line x1="8" y1="12.8" x2="8" y2="12.8" stroke-width="2" stroke-linecap="round"/>`;
export const VIEWPORT_ICON_RESET = `<path d="M3.1,5.5A5.5,5.5,0,1,1,2.8,10"/><polyline points="2,2 2,6 6,6"/>`;

export function setViewportIcon(button: HTMLButtonElement, svgInner: string): void {
    button.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none;">${svgInner}</svg>`;
}

/** Shared compact chrome used by local and video-backed viewports. */
export function makeViewportIconButton(
    svgInner: string,
    title: string,
    onClick: () => void,
): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button";
    button.title = title;
    setViewportIcon(button, svgInner);
    Object.assign(button.style, {
        width: "28px",
        height: "28px",
        minWidth: "28px",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "0",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "6px",
        background: "rgba(18, 18, 22, 0.75)",
        color: "rgba(255, 255, 255, 0.75)",
        cursor: "default",
        userSelect: "none",
        pointerEvents: "auto",
        boxSizing: "border-box",
        boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
        transition: "all 120ms ease",
    });
    button.addEventListener("mouseenter", () => {
        button.style.background = "rgba(18, 18, 22, 0.95)";
        button.style.borderColor = "rgba(255, 255, 255, 0.35)";
        button.style.color = "rgba(255, 255, 255, 0.98)";
    });
    button.addEventListener("mouseleave", () => {
        button.style.background = "rgba(18, 18, 22, 0.75)";
        button.style.borderColor = "rgba(255, 255, 255, 0.15)";
        button.style.color = "rgba(255, 255, 255, 0.75)";
    });
    button.addEventListener("click", onClick);
    return button;
}
