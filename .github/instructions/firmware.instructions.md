---
applyTo: "Firmware/**"
---

## Firmware source code
The firmware source code is located in the `Firmware/` directory and is split into separate subdirectories depending on the device architecture used.

### ATmega328P MCU-based devices
The firmware source code is located in the `Firmware/ATmega328P-based/` directory and is responsible for:
- Generating a user-predefined WSPR message based on the amateur radio callsign and the transmit power in dBm, for subsequent transmission on a predefined frequency.
- Calculating the QTH locator used when forming the WSPR message using data received from the onboard GPS module.
- Synchronizing the transmission timing of WSPR messages using data received from the onboard GPS module.
- Adding a random transmit frequency offset to prevent collisions with other WSPR transmitters operating in the same area.
- Indicating possible errors via the built-in LED indicators.
- Testing the functionality of the device's internal components and presenting the test results to the user using a separately flashed firmware image.

Devices based on the ATmega328P MCU do not support reconfiguration during operation. To apply new operating parameters (_amateur radio callsign, transmit power, transmission frequency_), the user must manually modify the firmware source code, rebuild it, and re-flash the device.

#### Build environment
- **Build system (_GitHub Actions_):** Arduino CLI.
- **Build configuration file (_GitHub Actions_):** `.github/workflows/firmware-build.yml`.

### ESP32-C3 SoC-based devices
The firmware is distributed to end users only in a signed and pre-encrypted form, which implies that it can be executed only on hardware devices that have explicitly provisioned Secure Boot v2 signing and Flash Encryption AES-XTS keys stored in the ESP32-C3 SoC eFuse.

In turn, the `Firmware/ESP32C3-based/` directory contains a `latest-stable.json` file with information about the current firmware version, download links to the binary files (_used for firmware updates via the BEACON.App application over USB and via the OTA mechanism_), and a SHA-256 checksum for validating the provided binary images.
