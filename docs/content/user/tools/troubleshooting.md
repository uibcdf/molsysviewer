# Troubleshooting

## I don’t see anything

- Make sure you called `v.show()` after loading.
- If you used `hide()`/`isolate()`, reset visibility with `v.show()`.
- If you hid the global view, call `v.whole.show()`.

## Units and boxes

MolSysViewer expects coordinates in Å. A periodic box, when present, should be provided as three vectors (Å).
