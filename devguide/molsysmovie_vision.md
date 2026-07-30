# VISION: `MolSysMovie` - Cinematic and VR Molecular Animation

> **Roadmap Status:** The core implementation has been promoted to **Pre-1.0**.
> See the archived [`molsysmovie_plan.md`](archive/molsysmovie_plan.md) for the concrete architecture
> and phased plan. The VR/360° export direction (Phase 4 of the original vision)
> remains Post-1.0.

## Problem Statement
`MolSysView` is excellently designed for interactive exploration, structural analysis, and static scene composition. However, creating complex animations—such as panning the camera, fading regions in and out, dynamically changing lighting, or animating measurements over time—requires a fundamentally different mental model. Forcing a timeline and keyframe logic into the interactive `MolSysView` would bloat the API and confuse the user experience.

## Proposed Solution: `MolSysMovie`
Introduce a new top-level class, `MolSysMovie` (or an extension module), dedicated entirely to programmatic animation, storytelling, and video export.

### Core Concepts

1.  **The Timeline & Keyframes:** Instead of changing state instantly, methods in `MolSysMovie` accept a timestamp or frame index.
    *   *Example:* `movie.camera.move_to(target=nucleo, start_time="0s", end_time="2s", easing="ease-in-out")`
    *   *Example:* `movie.measurements['m1'].fade_in(start_time="2s", duration="0.5s")`

2.  **The "Script" (Storyboarding):** Support for defining the entire animation sequence via a structured script.
    *   **Pythonic Scripting:** A list of event objects or a dedicated `Script` class.
    *   **External Serialization:** Ability to load a "Screenplay" from a `.yaml` or `.json` file. This allows researchers to edit the movie's timing without touching Python code.
    *   *Script Example:*
        ```yaml
        timeline:
          - time: 0.0
            action: camera_focus
            params: { target: 'protein', zoom: 1.2 }
          - time: 3.5
            action: show_region
            params: { tag: 'active_site', style: 'licorice', transition: 'fade', duration: 1.5 }
        ```

3.  **Smooth Transitions & Morphing:**
    *   **Representation Morphing:** Smoothly interpolate parameters (like stick radius or surface opacity) between two states.
    *   **Camera Paths:** Define complex camera trajectories using Splines (paths in 3D space) instead of just simple point-to-point moves.

4.  **Captions and Annotations:**
    *   Timed subtitles and "Lower Thirds" text overlays for scientific narration.
    *   Arrows or pointers that appear and disappear to guide the viewer's attention.

5.  **Cinematic Export Engine:**
    *   **Standard Video:** Export to `.mp4` or `.webm` using a headless rendering pipeline.
    *   **VR & 360° Video:** Equirectangular projection for immersive 3D experiences on YouTube VR or Oculus.
    *   **Audio Sync Stubs:** Metadata hooks to synchronize visual events with a background narration or music track.

## Benefits
- **Separation of Concerns:** Keeps `MolSysView` lightweight and focused on interactive analysis, while giving power users a dedicated tool for scientific communication and outreach.
- **Storytelling:** Allows researchers to craft a narrative, guiding the viewer's eye exactly where it needs to be at the exact right moment.
- **Cutting-Edge Outreach:** VR/360 video export would immediately set the library apart as a state-of-the-art tool for modern scientific education and public engagement.

## Implementation Path
- **Phase 1 (Data Model):** Design the Python-side timeline and keyframe registry.
- **Phase 2 (Mol* Integration):** Utilize Mol*'s `PluginAnimationLoop` and state interpolation features to translate Python keyframes into smooth WebGL transitions.
- **Phase 3 (Export):** Implement the headless frame-capture and FFmpeg stitching pipeline.
- **Phase 4 (VR):** Explore Mol*'s camera projection matrices to output equirectangular frames.
