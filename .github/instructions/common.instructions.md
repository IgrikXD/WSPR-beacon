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

## BEACON.App source code
The **BEACON.App source code** is located in the `App/` directory and is responsible for:
- Supporting communication between the hardware device (_WSPR-beacon_) and the desktop user application (_BEACON.App_) via USB (_Serial_) or Wi-Fi (_WebSocket_) connections using control commands in JSON format.
- Generating valid JSON control commands sent to the device (_WSPR-beacon_) to set the active transmission mode, run self-checks, and configure device parameters (_calibration, Wi-Fi connection_).
- Providing a device firmware update mechanism both via USB and through OTA updates.
- Ensuring the reliability of the user application by implementing integration and unit tests to verify the functionality of implemented features.

The application source code is organized into the following subpackages within `App/beaconapp/`:
- `transports/` - transport layer implementations.
- `ui/` - user interface widgets and graphical resources.
- `tests/` - test suite, split into `unit/` and `integration/` subdirectories.

**BEACON.App** is designed to work only with devices based on the **ESP32-C3 SoC**. Devices based on the **ATmega328P MCU** are not supported!

### Build environment
- **Build system:** PyInstaller, GitHub Actions.
- **Build configuration file (Linux, GitHub Actions):** `.github/workflows/app-build-linux.yml`.
- **Build configuration file (Windows, GitHub Actions):** `.github/workflows/app-build-windows.yml`.
- **Test configuration file (GitHub Actions):** `.github/workflows/app-tests.yml`.
- **Python standard:** 3.12.

## Firmware source code
The firmware source code is located in the `Firmware/` directory and is split into separate subdirectories depending on the device architecture used.

### ATmega328P MCU-based devices
The firmware source code is located in the `Firmware/ATmega328P-based/` directory and is responsible for:
- Generating a user-predefined WSPR message based on the amateur radio callsign and the transmit power in dBm, for subsequent transmission on a predefined frequency.
- Calculating the QTH locator used when forming the WSPR message using data received from the onboard GPS module.
- Synchronizing the transmission timing of WSPR messages using data received from the onboard GPS module.
- Adding a random transmit frequency offset to prevent collisions with other WSPR transmitters operating in the same area.
- Indicating possible errors via the built-in LED indicators.
- Testing the functionality of the device’s internal components and presenting the test results to the user using a separately flashed firmware image.

Devices based on the ATmega328P MCU do not support reconfiguration during operation. To apply new operating parameters (_amateur radio callsign, transmit power, transmission frequency_), the user must manually modify the firmware source code, rebuild it, and re-flash the device.

#### Build environment
- **Build system:** Arduino CLI, GitHub Actions.
- **Build configuration file (GitHub Actions):** `.github/workflows/firmware-build.yml`.

### ESP32-C3 SoC-based devices
The firmware is distributed to end users only in a signed and pre-encrypted form, which implies that it can be executed only on hardware devices that have explicitly provisioned Secure Boot v2 signing and Flash Encryption AES-XTS keys stored in the ESP32-C3 SoC eFuse.

In turn, the `Firmware/ESP32C3-based/` directory contains a `latest-stable.json` file with information about the current firmware version, download links to the binary files (_used for firmware updates via the BEACON.App application over USB and via the OTA mechanism_), and a SHA-256 checksum for validating the provided binary images.

# Critical rules
- **Never fabricate.** Do not invent information, do not make assumptions, and do not speculate about code, APIs, or functionality that you have not explicitly verified by reading the documentation files or performing searches.
- **Data-driven development.** All created solutions or responses must be based on factual data from technical documentation or search results.
- **Ask if something is unclear.** If any information is ambiguous, requires confirmation, or has multiple possible interpretations, clarify the points you need before continuing.
- **eFuse Safety.** Writing to eFuse is a permanent operation. Before suggesting any command that modifies eFuses (e.g., via espefuse.py), explicitly warn the user that this action is irreversible and could brick the device if keys or parameters are incorrect.
- **Look before you leap.** Before implementing a new functionality, search the `App/` (_if changes requested for the BEACON.App_) or `Firmware/` (_if changes requested for the firmware_) directory for existing implementations. Reuse existing modular components to maintain architectural consistency.

# Auxiliary tools
- **flake8**: The project uses flake8 for Python code linting. Refer to the `App/.flake8` file for the linting rules.