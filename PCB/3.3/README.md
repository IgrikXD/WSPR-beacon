# WSPR-beacon 3.3

## Device characteristics
**Platform:** ESP32-C3 SoC  
**Power amplifier:** Buffer amplifier based on the 74ACT244 IC  
**Output RF transformer:** Mini-Circuits ADT1-1+  
**RF connectors:** SMA  
**Feed line:** 50 Ohm coaxial cable  
**GPS antenna type:** Active, external  
**Maximum output power:** ~23 dBm  
**Supply voltage:** 5V (_USB-B, fuse-protected, 750 mA fuse_)  
| Mode                                                                       | Current consumption |
|----------------------------------------------------------------------------|---------------------|
| Standby (_GPS antenna not connected, Wi-Fi not connected, 50 Ohm load_)    |  91 mA              |
| Standby (_GPS antenna connected, Wi-Fi connected, 50 Ohm load_)            |  159 mA             |
| Active TX mode (_GPS antenna connected, Wi-Fi not connected, 50 Ohm load_) |  191 mA             |
| Active TX mode (_GPS antenna connected, Wi-Fi connected, 50 Ohm load_)     |  259 mA             |

## Firmware info
**Latest firmware version:** [wspr-beacon-2.0](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-firmware-2.0)  
**Supported transmission protocols:** WSPR  
**Configurable via user application:** Yes  

> [!NOTE]
> The firmware for device based on **ESP32-C3 SoC** is distributed only in **pre-encrypted** and **signed** form and runs **only** on devices where Flash Encryption and Secure Boot v2 keys have been explicitly programmed.
>
> **Any device you assemble yourself will not be able to run the publicly distributed encrypted firmware.** You can still use this project as a reference for developing your own firmware, or purchase a ready-made device that supports running the official firmware. To purchase a ready-made device, follow the [link](https://linktr.ee/wsprbeacon) to choose from the available options, or [contact me directly](https://t.me/igrikxd).
>
> Alternatively, you can use version [1.0](../1.0/README.md) and [2.0](../2.0/README.md) devices based on ATmega328P with the [wspr-beacon-1.1](../../Firmware/ATmega328P-based/wspr-beacon-1.1/) firmware, which is publicly available. These device versions **do not support [BEACON.App](../../App/README.md)** and can only be configured by modifying and rebuilding the firmware source code.

## PCB fabrication parameters
> [!WARNING]
>It is critical to strictly adhere to the specified parameters during PCB manufacturing!
Failure to do so may result in additional signal loss due to deviation of the RF line impedance from the calculated values. Impedance calculations were performed using the [Saturn PCB Design Toolkit](https://saturnpcb.com/saturn-pcb-toolkit/) for FR-4 material.

**Used PCB Material:** FR-4, TG150  
**PCB thickness:** 1.6 mm  
**Minimum hole size:** 0.3 mm  
**Surface finish:** HASL with lead  
**Via process:** Tented vias  
**Copper weight:** 1 oz  
