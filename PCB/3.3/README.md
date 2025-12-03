# WSPR-beacon 3.3

> [!NOTE]
>The source files for the PCB of this version of the device are not publicly available! For purchase inquiries, please [contact me directly](https://github.com/IgrikXD/WSPR-beacon#how-to-contact-me).

## Device characteristics
**Platform:** ESP32-C3 SoC  
**Power amplifier:** Buffer amplifier based on the 74ACT244 IC  
**Output RF transformer:** Mini-Circuits ADT1-1+  
**RF connectors:** SMA  
**Feed line:** 50 Ohm coaxial cable  
**GPS antenna type:** Active, external  
**Maximum output power:** ~23 dBm  
**Supply voltage:** 5V (_USB-B, fuse-protected, 750 mA fuse_)  
| Mode                                                          | Current consumption |
|---------------------------------------------------------------|---------------------|
| Standby (_GPS antenna not connected, Wi-Fi not connected_)    |  TBD mA             |
| Standby (_GPS antenna connected, Wi-Fi connected_)            |  TBD mA             |
| Active TX mode (_GPS antenna connected, Wi-Fi not connected_) |  TBD mA             |
| Active TX mode (_GPS antenna connected, Wi-Fi connected_)     |  TBD mA             |

## Firmware info
**Latest firmware version:** [wspr-beacon-2.0](../../Firmware/wspr-beacon-2.0/)  
**Supported transmission protocols:** WSPR  
**Configurable via user application:** Yes  

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
