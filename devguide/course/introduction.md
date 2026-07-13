# Introduction to the MolSysViewer Master Course: Philosophy & Tone

This document defines the pedagogical philosophy, tone, and formatting standards for the **Introduction to MolSysViewer** master course. This curriculum is designed to teach users how to transition from interactive molecular visualization to reproducible, programmatic scientific states.

---

## 🎯 1. Core Philosophy: "Do Not Let Interaction Outrun Reproducibility"

In computational structural biology, molecular visualization serves two main phases:
1. **Interactive and Exploratory Phase:** Exploring binding pockets, making distance measurements, or testing orientations.
2. **Reproducible and Sharing Phase:** Saving, scripting, and communicating results in a publication-quality or pipeline-safe format.

Most molecular viewers treat these two phases as disconnected. In contrast, **MolSysViewer** is designed as a *reproducible molecular workbench*. The core philosophy of this course is:
> **Every interactive GUI action has a programmatic API equivalent, and every visual exploration must be captured as reproducible Python state.**

Therefore, the course teaches users not just how to click on atoms, but how to:
* Freeze interactive selections into named registries.
* Replay visual scenes from saved scripts.
* Programmatically manipulate structures (coordinates) and export scenes as standalone interactive HTML.

---

## 🗣️ 2. Writing Tone and Voice

To maintain consistency with the rest of the MolSysSuite documentation, all course modules must follow these editorial conventions:

* **Direct and welcoming:** Write in the second person ("you") and use active verbs (e.g., *"You will load..."* instead of *"The user should load..."*).
* **Science-first:** Always lead with the "why" (the biological or physical question) before the "how" (the code or UI actions).
* **Concise and Scannable:** Keep paragraphs short (1-3 sentences). Use bullet points and bold highlights for critical terms.
* **Terminology alignment:** Always match API and GUI names exactly (e.g., use `active_selection`, `regions`, `layers`, and `FigureSpec` as they are written in code).

---

## 🏗️ 3. Pedagogical Structure of a Module

Every unit (Jupyter Notebook) in this course must follow a structured **"Hero's Journey"** narrative:

### Section 1: Science Hook & Objectives
Hook the reader with a concrete biological or chemical problem (e.g., *"How do we identify a binding pocket?"*). Clearly list 3-4 actionable learning objectives.

### Section 2: Setting the Stage
Initialize the viewer and load the training molecular systems. This section uses pre-packaged demo datasets (like Crambin `1CRN` or Pentalanine) to avoid external network dependencies.

### Section 3: Interactive UX Action
Instruct the student to perform a manual action in the 3D canvas (e.g., click a residue, right-click to create a measurement, or adjust a clipping plane slider).

### Section 4: Programmatic API Equivalent
Show how to capture that manual action or reproduce it programmatically using the Python API (e.g., calling `active_selection.save()`, `view.new_region()`, or `view.measurements.add_distance()`).

### Section 5: Audit & Diagnostics
Teach the student how to check the internal state of the viewer (e.g., calling `view.info()` or reading `load_blocks` and `js_logs`) to verify their actions.

### Section 6: Key Takeaway
A brief summary explaining the scientific value of what was learned and a transition to the next unit.
