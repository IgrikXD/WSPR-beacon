# Firmware instructions

For devices based on the **ESP32-C3 SoC** ([_version 3.3 and later_](https://github.com/IgrikXD/WSPR-beacon/blob/master/PCB/3.3/README.md)), firmware is updated automatically using the [BEACON.App] user application.

> [!NOTE]
> The firmware for device based on **ESP32-C3 SoC** is distributed only in **pre-encrypted** and **signed** form and runs **only** on devices where Flash Encryption and Secure Boot v2 keys have been explicitly programmed.
>
> **Any device you assemble yourself will not be able to run the publicly distributed encrypted firmware.** You can still use this project as a reference for developing your own firmware, or purchase a ready-made device that supports running the official firmware. To purchase a ready-made device, follow the [link](https://linktr.ee/wspr_beacon) to choose from the available options, or [contact me directly](https://t.me/igrikxd).
>
> Alternatively, you can use version [1.0](https://github.com/IgrikXD/WSPR-beacon/blob/master/PCB/1.0/README.md) and [2.0](https://github.com/IgrikXD/WSPR-beacon/blob/master/PCB/2.0/README.md) devices based on ATmega328P with the [wspr-beacon-1.1](https://github.com/IgrikXD/WSPR-beacon/tree/master/Firmware/wspr-beacon-1.1) firmware, which is publicly available. These device versions **do not support [BEACON.App]** and can only be configured by modifying and rebuilding the firmware source code.

## Firmware update

To check for available firmware updates, connect the device and launch [BEACON.App]. Then go to the **Self-check** tab and click the **Update** button next to the **Firmware version** field. If an update is available, the new firmware version will be downloaded and installed automatically. After that, the device will reboot and will be ready to use.

[BEACON.App]: https://github.com/IgrikXD/WSPR-beacon/blob/master/App/README.md