---
applyTo: "**/*"
---

# Project description
The project is an open implementation of a hardware-software platform used for transmitting amateur WSPR messages.

The project is divided into the following main logical directories:
- `App/` - contains the source code of the **BEACON.App** user application, used with devices based on the **ESP32-C3 SoC**. It also includes integration tests, unit tests, and build documentation for different operating systems.
- `Firmware/` - contains firmware-related files for devices based on the **ATmega328P MCU** and the **ESP32-C3 SoC**. For ATmega328P MCU, it includes firmware source code, build documentation, and end-user documentation. For ESP32-C3 SoC, it contains firmware version metadata and download links for binary images. The ESP32-C3 SoC firmware is proprietary and stored in a separate private repository that is not accessible to end users.
- `PCB/` - contains Gerber manufacturing files, schematics, bills of materials (_BOM_), and manual assembly instructions for a specific device revision.
- `Resources/` - contains graphical assets used in the project documentation.

The project is developed using a modular architecture with a clear separation of responsibilities between individual components.

# Critical rules
- **Never fabricate.** Do not invent information, do not make assumptions, and do not speculate about code, APIs, or functionality that you have not explicitly verified by reading the documentation files or performing searches.
- **Data-driven development.** All created solutions or responses must be based on factual data from technical documentation or search results.
- **Ask if something is unclear.** If any information is ambiguous, requires confirmation, or has multiple possible interpretations, clarify the points you need before continuing.
- **eFuse Safety.** Writing to eFuse is a permanent operation. Before suggesting any command that modifies eFuses (e.g., via espefuse.py), explicitly warn the user that this action is irreversible and could brick the device if keys or parameters are incorrect.
- **Look before you leap.** Before implementing a new functionality, search the `App/` (_if changes requested for the BEACON.App_) or `Firmware/` (_if changes requested for the firmware_) directory for existing implementations. Reuse existing modular components to maintain architectural consistency.

# Related instruction files
- [beaconapp.instructions.md](./beaconapp.instructions.md) — **BEACON.App** architecture, threading model, logging, testing conventions, and auxiliary tools (_applies to `App/**`_).
- [firmware.instructions.md](./firmware.instructions.md) — Firmware source code structure and build environment for ATmega328P MCU based and ESP32-C3 SoC based devices (_applies to `Firmware/**`_).
- [python.instructions.md](./python.instructions.md) — Python naming conventions, error handling, code formatting, docstrings, import ordering, type hints, and best practices (_applies to `**/*.py`_).
