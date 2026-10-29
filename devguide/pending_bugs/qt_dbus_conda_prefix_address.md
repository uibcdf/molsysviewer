---
summary: Qt startup reports an invalid D-Bus system address in Conda prefixes containing @.
issue: uibcdf/molsysviewer#278
status: open
opened: 2026-10-29
closed:
severity: low
verification: reproduced
area: [standalone, environment, diagnostics]
guard:
normative:
blocked_by: []
supersedes: []
---

# Invalid D-Bus system address in a relocated Conda prefix

## What

The maintainer reports these diagnostics on every `molsysviewer-qt 1TCD --demo`
launch, while the visible window renders and appears to function adequately:

```text
GBM is not supported with the current configuration. Fallback to Vulkan rendering in Chromium.
Failed to connect to the bus: In D-Bus address, character '@' should have been escaped
```

The D-Bus message is a reproducible connection failure. The GBM message is a
separate renderer-selection diagnostic; this report does not establish a GPU
failure, performance loss or a broken molecular workflow.

## How

Linux GNOME/Wayland, canonical Qt/PySide6 6.11.2, conda-forge `dbus` 1.16.2
`he8c428d_2`, environment `molsyssuite@uibcdf_3.14`. The installed
`lib/libdbus-1.so.3.38.3` contains this default address (parent path abbreviated):

```text
unix:path=<env-parent>/molsyssuite@uibcdf_3.14/var/run/dbus/system_bus_socket
```

`DBUS_SYSTEM_BUS_ADDRESS` is unset. The session address points to the existing
`/run/user/<uid>/bus` socket and has no `@`. The default system address contains
an unescaped `@`, which the [D-Bus address grammar](https://dbus.freedesktop.org/doc/dbus-specification.html#addresses)
rejects; its prefix-local socket also differs from the host socket.

An isolated ctypes probe loads that exact library, declares the `DBusError`
structure and public `dbus_error_init`, `dbus_bus_get`, `dbus_connection_unref`
and `dbus_error_free` signatures, and requests session (0) and system (1)
connections in fresh child processes. Outside the sandbox, the results are:

| Child environment | Session | System |
| --- | --- | --- |
| System override unset | connected | invalid-address error naming `@` |
| `DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket` | connected | connected |

The local probe is retained at
`.pytest_cache/modern-qt-20261029/dbus_probe.py`; this is diagnostic evidence,
not a durable regression guard or an installed-Viewer qualification. No Viewer
or Qt import is needed to reproduce the failure. The sandbox blocks the valid
bus socket, so its permission failure is not a native connection result.

For a process-local application check on this host, use:

```bash
DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket molsysviewer-qt 1TCD --demo
```

The isolated library check passes with this address. The full Viewer launch
with it remains a separate observation; no application success is inferred.

## Why

A library/package fallback makes a functioning application emit a persistent
error and prevents that system-bus connection. The provider/package owns the
relocated default; Viewer owns its consumer diagnosis and any justified launcher
integration. Related #109 tracks canonical Qt adoption, a separate boundary.

## What was refuted

- The error reproduces without Viewer or Qt, so it is not caused by the new
  native header or the molecular rendering logic.
- The native session bus connects successfully. This is not evidence that the
  entire desktop D-Bus session is unavailable.
- Vulkan fallback does not imply CPU rendering. Qt documents its NVIDIA route
  in [Qt WebEngine Features](https://doc.qt.io/qt-6.10/qtwebengine-features.html#nvidia-on-linux).
- Disabling graphics acceleration, globally suppressing stderr or renaming the
  development environment is not required to isolate the address defect.

## Next action and acceptance

Choose the provider feedback and consumer disposition before a permanent fix.
No upstream issue has been filed yet. A documented process-local setting may
suffice; a host integration must preserve explicit user addresses, avoid import
side effects and remain bounded to the actual Linux/library condition. Guard
prefixes containing `@`, existing settings, an absent host bus and unaffected
hosts if code is introduced. Retain real Qt rendering checks and visible genuine
errors. Do not claim this issue is fixed from the isolated probe alone.
