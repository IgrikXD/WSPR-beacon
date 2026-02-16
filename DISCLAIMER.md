# Licensing & terms of use
This project follows a multi-license model. By using any part of this project, you agree to the following terms:

## License matrix
| Component	                             | License	                         | Commercial Use                 |
|----------------------------------------|-----------------------------------|--------------------------------|
| Control Software (_Source, binaries_)  | GNU GPL v3.0	                     | Allowed (_under GPLv3 terms_)  |
| Hardware (_Schematics, PCB_)           | CC BY-NC-SA 4.0                   | Prohibited                     |
| Firmware (_ATmega328P based_)	         | GNU GPL v3.0                      | Allowed (_under GPLv3 terms_)  |
| Firmware (_ESP32-C3 based_)	         | Proprietary / EULA                | Prohibited                     |
| Project Name & Logo	                 | Trademark / Intellectual Property | Prohibited                     |

## Commercial use restrictions
Usage of the following materials for commercial purposes is strictly prohibited without prior written consent from the author:
- **Hardware.** Production, assembly, and sale of PCBs, kits, or finished devices based on the provided designs.
- **ESP32-C3 firmware.** Distribution, flashing onto devices for sale, or bundling with commercial products.
- **Branding.** Using the name "WSPR-beacon", the author's nickname, or associated logos for marketing any products or services.
- **Documentation.** Reproduction of project documentation for commercial manuals or guides.

# Important
This device is radio transmitting equipment and is intended for experimental use by licensed radio amateurs. The user is responsible for: 
- Complying with local laws and radio regulations (_operating frequencies, output power_). 
- Possession of a valid amateur radio license and callsign.
- Proper antenna installation and output signal filtering.

The seller/designer is not liable for the consequences of misuse, modifications, incorrect configuration, or operation of the device, including interference, damage, or potential legal issues, to the extent permitted by applicable law.

## Intended use
The device is an amateur-radio beacon (_transmitter_) for experimental operation on the following amateur bands: **2200m, 600m, 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m, 4m, 2m**.

## Output power
Output power is approximately **~23 dBm** (_~200 mW_) and is not a guaranteed or calibrated value. Actual performance depends on the power supply, temperature, load, filtering, and the antenna used.

# Warnings and user responsibility
The user is solely responsible for:
- Complying with the laws and regulatory requirements of their country/region, including holding a valid license and amateur radio callsign.
- Selecting the correct frequency/sub-band, observing output power and duty-cycle limits.
- Meeting any other requirements imposed by the local regulator.

## Interference and cessation of operation
If interference to other radio services/devices occurs, the user must immediately stop transmitting and eliminate the cause (_incorrect device configuration, insufficient output filtering, unsuitable antenna, high SWR, excessive output power, improper transmitter placement, etc._).

## Modifications and self-repair
Any changes to the internal hardware of the device, as well as any changes to the software/firmware, are performed at the user’s own risk and may result in non-compliance with local regulations, unintended emissions (_interference_), and device damage. If the device design or software has been altered, the seller/designer may refuse further support and warranty service.

## Safety
The device is not intended for use in systems where failure could affect life or health (_aviation, medical, emergency/critical services, etc._). Use only properly rated and working power supplies and follow basic electrical and RF safety precautions.

## Limitation of liability
The seller/designer is not liable for any direct or indirect losses, damage, interference, data loss, or legal consequences arising from misuse, incorrect configuration, modifications, or operation of the device, to the extent permitted by applicable law.

# Returns and hardware defects
If, within **14 calendar days** from receipt of the device, a hardware defect attributable to the manufacturer/designer (_factory defect_) is discovered, a return is possible, or repair/replacement may be provided by mutual agreement. To submit a claim, the user must contact the manufacturer/designer and provide a description of the issue (_photos/videos upon request_) and the conditions under which it occurs.

## Exclusions
The following are not considered factory defects and are not covered:
- Incorrect wiring/power, overvoltage, overheating, moisture/corrosion.
- Mechanical damage, signs of drops/impacts.
- Device damage caused by operating into a mismatched load/antenna.
- Device damage caused by connecting external amplifiers/modules.
- Device damage caused by static discharge (_ESD_) or lightning.
- Disassembly, alterations, self-repair, software/firmware modifications (_including via OTA_) that change the device’s operating mode.

## Statutory rights
Nothing in these terms limits any consumer rights that cannot be excluded or limited under applicable law.

By using the device, you confirm that you understand the risks listed above and agree to comply with local laws and regulations.
