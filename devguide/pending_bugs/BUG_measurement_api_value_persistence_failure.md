# BUG: Measurements created via API lack numerical value in `info()`

## Description
When a distance or angle is created programmatically using `view.measurements.add_distance()` or `add_angle()`, the `value` field in `view.measurements.info()` remains `None`. This is because the numerical result (calculated by Mol*) is not being synchronized back to the Python-side message history for API-driven events.

## Steps to Reproduce
1. Load a structure.
2. Create a distance via API: `view.measurements.add_distance(selection_a='...', selection_b='...')`.
3. Check `view.measurements.info()`.
4. **Observed Result:** `{'value': None, ...}`. (Interactive measurements DO have a value).

## Technical Analysis
In `molsysviewer/measurements.py`, the `_send_measurement` method records the operation in history before sending it to the frontend. Since the calculation happens on the GPU/JS side, Python does not know the result at the time of recording. The library currently lacks a "callback" or an update mechanism to inject the calculated value into the already recorded history message once Mol* has performed the measurement.
