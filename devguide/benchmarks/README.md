# 🚀 MolSysViewer Performance Benchmarks

This directory contains the developer documentation for the native molecular benchmarking suite of MolSysViewer.

## 🎯 Purpose and Philosophy

As MolSysViewer approaches its 1.0 release, ensuring high-frequency rendering and data transfer speeds is of paramount importance. The benchmarking suite has been designed with three core philosophies:
1. **Zero Mocks**: We use actual built-in demo systems (`dialanine`, `chicken_villin_HP35`, `1TCD`) representing real-world chemical structures and trajectories to get authentic timing metrics.
2. **Zero Runtime Intrusion**: The benchmarking module (`molsysviewer.tools.benchmark`) is strictly separated from production execution and has zero impact on core library startup or run speed.
3. **Observation-Driven Optimization**: Every telemetry or validation framework introduced (such as `smonitor` signal tracking and `argdigest` validation) must be continuously measured to keep overhead minimal.

---

## 📊 Measured Suites

The benchmarking engine measures performance across four critical areas:

### 1. Topology & Structure Loading
Measures the duration (in milliseconds) required to load distinct structural datasets from the H5MSM package resources into a fresh viewer instance.
- **Dialanine**: Extremely small dipeptide (22 atoms, 1 structure).
- **1TCD**: Medium-sized protein structure (3,803 atoms, 1 structure).
- **Chicken Villin HP35**: Medium-sized trajectory with multiple frames (596 atoms, 10 structures).

### 2. Coordinate Transfer Performance
Evaluates the speed of reading and writing coordinates over the Python-JS boundary. High performance here ensures smooth trajectory playback and real-time visualization updates.
- **Get Coordinates**: Serializing positions out of the loaded structure database.
- **Set Coordinates**: Parsing coordinate updates and rebuilding the scene.

### 3. JSON/Jupyter Bridge Serialization Latency
High-frequency WebSocket events (e.g. hover events, camera update events) generate high-volume traffic. This benchmark measures the cost of encoding typical MolSysViewer message payloads into JSON strings using the python standard library (`json.dumps`).

### 4. Telemetry & Validation Overhead
Quantifies the exact overhead introduced by our telemetry and signature validation frameworks. We compare the average time to execute a collection of representative public API operations (`new_region`, `zoom`, `get_camera_snapshot`, `set_camera_snapshot`) across four configurations:
1. **Baseline**: SMonitor disabled & ArgDigest bypassed.
2. **SMonitor-only**: SMonitor enabled & ArgDigest bypassed.
3. **ArgDigest-only**: SMonitor disabled & ArgDigest active.
4. **Full Overhead**: Both SMonitor and ArgDigest fully enabled.

---

## 🛠️ How to Run the Benchmarks

To execute the benchmarks from python:

```python
import molsysviewer as msv

# Run benchmarks (runs 50 iterations by default and outputs a Markdown report)
report = msv.tools.benchmark.run_benchmarks(iterations=50)
print(report)
```

From terminal, you can run:
```bash
python -c "import molsysviewer as msv; print(msv.tools.benchmark.run_benchmarks(50))"
```

---

## 📈 Current Performance Status

The latest performance runs (conducted on 2026-05-22 with 50 iterations, and 5 for file loading) are summarized below:

### 📦 1. Topology & Structure Loading Speed
Measures fresh file loading duration (H5MSM structure files from demo package).

| System | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) |
| :--- | :---: | :---: | :---: | :---: |
| `dialanine` | 354.39 | 4046.54 | 1126.73 | 1460.13 |
| `1TCD` | 422.61 | 551.85 | 465.83 | 45.98 |
| `chicken_villin_HP35` | 452.68 | 728.14 | 579.79 | 102.57 |

*Note: The high maximum and standard deviation on the `dialanine` loading are caused by the initial python import and library warming during the first iteration. (This note used to also credit a "dynamic compiler JIT cache load (Numba/MolSysMT)". **MolSysMT was rewritten in Rust for 1.0 and no longer uses Numba**, so that component of the variance no longer exists and these figures predate the change.)*

### 🔄 2. Coordinate Transfer Performance
Measures coordinate extraction (`get_coordinates`) and replacement/scene-rebuild (`set_coordinates`).

| Operation | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) |
| :--- | :---: | :---: | :---: | :---: |
| `dialanine_get` | 17.98 | 35.31 | 21.53 | 3.91 |
| `dialanine_set` | 204.61 | 327.11 | 232.06 | 30.18 |
| `villin_get` | 20.40 | 36.35 | 24.32 | 3.61 |
| `villin_set` | 310.29 | 618.38 | 360.78 | 74.27 |

*Note: Setting coordinates triggers the central scene-rebuilding and canvas-redrawing logic, which scales with the number of atoms and loaded frames.*

### ⚡ 3. JSON Serialization Latency
Measures serialization cost (`json.dumps`) of representative outbound WebSocket payloads.

| Payload Type | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) |
| :--- | :---: | :---: | :---: | :---: |
| `camera_snapshot` | 0.0061 | 0.0572 | 0.0090 | 0.0081 |
| `coordinates_500atoms` | 0.4825 | 1.2626 | 0.6930 | 0.2481 |

### 🚀 4. Telemetry & Validation Overhead
Measures overhead on a sequence of API calls (`new_region`, `zoom`, `get_camera_snapshot`, `set_camera_snapshot`).

| Telemetry Configuration | Min (ms) | Max (ms) | Mean (ms) | StdDev (ms) | Overhead (ms) | Slowdown (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Baseline (None)` | 18.73 | 34.66 | 21.06 | 2.42 | — | — |
| `SMonitor-only` | 20.22 | 52.45 | 25.54 | 7.36 | +4.48 | 21.3% |
| `ArgDigest-only` | 21.36 | 47.18 | 26.30 | 5.60 | +5.25 | 24.9% |
| `Full Telemetry` | 23.68 | 45.32 | 29.44 | 5.06 | +8.38 | 39.8% |

---

## 🚀 Future Roadmap

Future iterations of the benchmarking framework will address:
1. **Remote Fetching Overhead**: Evaluating the overhead of caching and streaming coordinate chunks from remote servers (e.g., PDB, h5msm-web).
2. **Headless Browser Rendering**: Integrating playwright/headless chromium render timings to measure visual canvas frame-rates and GPU bottlenecks directly.
3. **WebSocket Bridge Round-Trips**: Measuring round-trip times for complex request-response operations across active Jupyter connections.
