# Developer Guide

Welcome to the technical documentation for **MolSysViewer**. This guide is intended for developers who wish to contribute to the library or understand its inner workings.

## Source of Truth

For development work in this repository, `devguide/` is the source of truth.
Every meaningful development step should be reflected here as a checkpoint
covering:

- decisions,
- status,
- immediate plan,
- criteria/invariants,
- perspectives and ideas.

## Contents

1. [**Architecture**](architecture.md)
   - The Python/JS bridge, Mol* integration, and messaging protocol.
2. [**Digestion and Dependencies**](digestion_and_dependencies.md)
   - Using ArgDigest for validation and DepDigest for environment robustness.
3. [**SMonitor Integration**](smonitor.md)
   - Diagnostics, catalog rules, and telemetry signals.
4. [**Roadmap**](roadmap.md)
   - Strategic goals and upcoming development phases.
5. [**Checkpoints**](checkpoints.md)
   - Running log of technical decisions and progress status.

## Standards and Conventions

This project strictly adheres to the UIBCDF software engineering standards. Please refer to the root `*_GUIDE.md` files for the canonical documentation of each infrastructure tool.
