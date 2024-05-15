# wspr-beacon

A small hardware device for transmitting WSPR messages based on the SI5351 IC. The device has a built-in TCXO to eliminate frequency drift of SI5351, built-in GPS module for operation with active GPS antennas and transmission time synchronization and a simple amplifier based on a single BS170 transistor. PCB is made on based on SMD components and adapted for installation in an aluminum enclosure with dimensions 80 x 50 x 20 mm.

## Current development progress:
[![Progress](https://img.shields.io/badge/wspr--beacon-not%20tested-red.svg?longCache=true&style=for-the-badge)](https://oshwlab.com/igrikxd/wspr-beacon)&nbsp;[![Progress](https://img.shields.io/badge/firmware%20version-0.1-blue.svg?longCache=true&style=for-the-badge)](./Firmware)&nbsp;[![Progress](https://img.shields.io/badge/pcb%20version-1.0-blue.svg?longCache=true&style=for-the-badge)](./EasyEDA)

The [ESP WSPR](https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/) firmware is taken as a reference and adapted for use with the Atmega328P.

**Main changes in the firmware:** NTP synchronization has been replaced by GPS synchronization, changed the detail of displaying status information while the program is running, code refactoring.   

The correct encoding of the transmitted WSPR message was verified by decoding the transmission through the locally located Airspy R2 SDR receiver and the [WSJT-X](https://wsjt.sourceforge.io/wsjtx.html) application.

## Basic characteristics of the WSPR-beacon:
**RF connectors:** SMA  
**Feed line:** 50 Ohm coaxial cable  
**Output power:** XX dBm  
**Supply voltage:** 5V, USB-B  
**Used PCB Material:** FR-4  
**PCB thickness:** 1.6 mm  
**PCB copper weight:** 1 oz  

## How to use this repository?
The [Firmware](./Firmware/) folder contains software required for the device operation and firmware instructions. The [Schematics](./Schematics/) directory contains the device schematic file in _.pdf_ format. The [Gerbers](./Gerbers/) directory contains files necessary for ordering PCB fabrication at the factory.

Additionally, you can find information about the [list of required components](./Components-list.md), [assembly guide](./Assembly-guide.md), and [operating instructions](./Usage-guide.md).

## Resources:
[ESP WSPR – Simple and Inexpensive WSPR Transmitter - Ankara Telsiz ve Radyo Amatörleri Kulübü Derneği](https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/)  
[K1FM-WSPR-TX - GitHub](https://github.com/adecarolis/K1FM-WSPR-TX)  
[A Little WSPR Beacon (Aren’t They All Little?) – Dave Richards AA7EE](https://aa7ee.wordpress.com/2023/02/26/a-little-wspr-beacon-arent-they-all-little/)