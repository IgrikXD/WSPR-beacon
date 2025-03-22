# WSPR-beacon 1.0

## Device characteristics
**Platform:** Atmega328 MCU  
**Power amplifier:** Transistor amplifier, based on BS170  
**Output RF transformer:** Bifilar transformer based on an FT37-43 core  
**RF connectors:** SMA  
**Feed line:** 50 Ohm coaxial cable  
**GPS antenna type:** Active, external  
**Maximum output power:** ~23 dBm  
**Supply voltage:** 5V (_USB-B, fuse-protected, 600 mA fuse_)  
| Mode                                  | Current consumption |
|---------------------------------------|---------------------|
| Standby (_GPS antenna not connected_) |  70 mA              |
| Standby (_GPS antenna connected_)     |  86 mA              |
| Active TX mode (_PA bias 2.5V_)       |  107 mA             |
| Active TX mode (_PA bias 4.6V_)       |  224 mA             |

## Firmware info
**Latest firmware version:** [wspr-beacon-1.1](../../Firmware/wspr-beacon-1.1/)  
**Supported transmission protocols:** WSPR  
**Configurable via user application:** No  

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
