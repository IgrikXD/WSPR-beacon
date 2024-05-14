# wspr-beacon

A small hardware device for transmitting WSPR messages based on the SI5351 IC and using GPS to synchronize the transmission time.  

The project has a [schematic](./Schematics) and [GERBER](./Gerbers) files for making a PCB of the finished device based on SMD components and installation in an aluminum case with dimensions 80 x 50 x 20 mm. Based on the submitted files, you can order PCB manufacturing at the factory ([PCBWay], [JLCPCB]). The device has a built-in TCXO to eliminate frequency drift of SI5351, built-in GPS module for operation with active GPS antennas and a simple amplifier based on a single BS170 transistor.

## Current development progress:
[![Progress](https://img.shields.io/badge/wspr--beacon-not%20tested-red.svg?longCache=true&style=for-the-badge)](https://easyeda.com/IgrikXD/wspr-beacon)&nbsp;[![Progress](https://img.shields.io/badge/firmware%20version-0.1-blue.svg?longCache=true&style=for-the-badge)](./Firmware)&nbsp;[![Progress](https://img.shields.io/badge/pcb%20version-1.0-blue.svg?longCache=true&style=for-the-badge)](./EasyEDA)

The [ESP WSPR](https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/) firmware is taken as a reference and adapted for use with the Atmega328P.

**Main changes in the firmware:** NTP synchronization has been replaced by GPS synchronization, changed the detail of displaying status information while the program is running, code refactoring.   

The correct encoding of the transmitted WSPR message was verified by decoding the transmission through the locally located Airspy R2 SDR receiver and the [WSJT-X](https://wsjt.sourceforge.io/wsjtx.html) application.

## How to use?

Enter your amateur radio call sign, the first 4 characters of your QTH locator and the transmitted power value to generate a correct WSPR message:
```sh
#define WSPR_CALL                 "XX0YYY"
#define WSPR_LOC                  "XX00"
#define WSPR_DBM                   10
```

## Firmware instruction

### Select the Board:
Now, in the "_Tools_" -> "_Board_" menu, choose "_Arduino Nano_".

### Choose the Port:
Connect the device to your computer via USB. Then, in the "_Tools_" -> "_Port_" menu, select the corresponding port.

### Upload an Firmware:
Click the "_Upload_" button in the Arduino IDE to compile and upload your program to the device.

## Resources:
[ESP WSPR – Simple and Inexpensive WSPR Transmitter - Ankara Telsiz ve Radyo Amatörleri Kulübü Derneği](https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/)  
[K1FM-WSPR-TX - GitHub](https://github.com/adecarolis/K1FM-WSPR-TX)  
[A Little WSPR Beacon (Aren’t They All Little?) – Dave Richards AA7EE](https://aa7ee.wordpress.com/2023/02/26/a-little-wspr-beacon-arent-they-all-little/)

[PCBWay]: <https://www.pcbway.com/>
[JLCPCB]: <https://jlcpcb.com/>