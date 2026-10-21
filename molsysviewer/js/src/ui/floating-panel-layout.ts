/**
 * Initial floating Studio dimensions in CSS pixels, independent of window mode.
 * Reserve vertical room for normal/fullscreen controls and cap large-screen
 * defaults; manual bounds belong to the shell. Popup consumers add window chrome
 * and apply their own screen limits. Fullscreen is scoped to the caller's host.
 */
export function getFloatingPanelSize(hostWidth: number, hostHeight: number, fullscreen = false): { width: number; height: number } {
    return {
        width: Math.max(0, Math.min(hostWidth * 0.86, 1200, hostWidth - 20)),
        height: Math.max(0, Math.min(hostHeight * 0.88, 940, hostHeight - 2 * Math.min(fullscreen ? 72 : 48, hostHeight * 0.2))),
    };
}
