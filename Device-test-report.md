# WSPR-beacon device test report

This section provides information about the device's performance during long-distance WSPR message transmission. Data on transmitted and decoded WSPR messages are taken from the [WSPR Rocks!](http://wspr.rocks/)

For each transmission range, a visualized report with a list of all spots is available. To view the visualization, click on the distance in the "_Max distance to receiver_" column.

> [!NOTE]
>During testing of the device, the antenna used was tuned to the resonant frequency using the NanoVNA vector network analyzer.  
>
>**The efficiency of an antenna's performance largely depends on its installation conditions!** In addition to tuning the antenna to achieve the minimum SWR value, the quality of transmission is also influenced by: the height of the antenna installation, the orientation of the antenna in space, the presence of dense urban development with a large amount of electromagnetic interference, and the presence of dense forests absorbing emitted radio waves. **Please, when installing the antenna, to achieve maximum performance, consider all possible factors affecting the efficiency of radio transmission!**

**Power source used:** Mi Power Bank Pro PLM07ZM  
**Coordinates of the antenna installation site:** [52.1958, 20.7581](https://maps.app.goo.gl/dVwvhpxdYiYVqSht5)

### [PCB version 1.0](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-1.0) with BS170 field-effect transistor amplifier:

| Firmware version | TX frequency | TX time (CET) | PA bias | Used antenna     | SNR | Drift | Max distance to receiver                            |
|------------------|--------------|---------------|---------|------------------|-----|-------|-----------------------------------------------------|
| 1.0              | 5.2887 MHz   | 21:02 - 21:32 | 2.508V  | [Windcamp Gipsy] | -22 | 0     | [3898 km](https://kmzview.com/oLjDi97JSwUt4asd76AU) |
| 1.0              | 7.0401 MHz   | 19:04 - 19:34 | 2.508V  | [Windcamp Gipsy] | -16 | 0     | [2849 km](https://kmzview.com/QG6PJxd4n7pIKje1FPqJ) |
| 1.0              | 10.1402 MHz  | 17:32 - 18:02 | 2.508V  | [Windcamp Gipsy] | -4  | 0     | 2849 km                                             |
| 1.0              | 14.0971 MHz  | 15:10 - 15:40 | 2.508V  | [Windcamp Gipsy] | -26 | 0     | 1797 km                                             |
| 1.1              | 5.2887 MHz   | 21:36 - 22:06 | 2.508V  | [Windcamp Gipsy] | -23 | 0     | [3898 km](https://kmzview.com/xUuaNxEI2ygnvwKXAeCg) |
| 1.1              | 7.0401 MHz   | 19:38 - 20:08 | 2.508V  | [Windcamp Gipsy] | -21 | 0     | [2043 km](https://kmzview.com/ISVBaADCSzKYEnMFMueG) |
| 1.1              | 10.1402 MHz  | 16:56 - 17:26 | 2.508V  | [Windcamp Gipsy] | -4  | 0     | 2849 km                                             |
| 1.1              | 14.0971 MHz  | 14:34 - 15:02 | 2.508V  | [Windcamp Gipsy] | -6  | 0     | 1721 km                                             |

### [PCB version 2.0](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-pcb-2.0) with SN74ACT244PWR buffer amplifier:

| Firmware version | TX frequency | TX time (CET) | Used antenna     | SNR | Drift | Max distance to receiver                            |
|------------------|--------------|---------------|------------------|-----|-------|-----------------------------------------------------|
| 1.1              | 5.2887 MHz   | 22:10 - 22:40 | [Windcamp Gipsy] | -19 | 0     | [3898 km](https://kmzview.com/C4Vx5jR3cHyAeCuntnj1) |
| 1.1              | 7.0401 MHz   | 20:14 - 20:44 | [Windcamp Gipsy] | -13 | 0     | [2849 km](https://kmzview.com/xsiJUzFLm3NW8JmR7vqk) |
| 1.1              | 10.1402 MHz  | 16:16 - 16:46 | [Windcamp Gipsy] | -6  | 0     | [2849 km](https://kmzview.com/oxZQNGHUcbKiORljG38z) |
| 1.1              | 14.0971 MHz  | 13:40 - 14:10 | [Windcamp Gipsy] | -19 | 0     | [3898 km](https://kmzview.com/sHu8uqWiTvDA2ghHyNwx) |

## Device testing reports from users

This section provides information about the device's performance during long-distance WSPR message transmission based on real user feedback.

### [PCB version 1.0](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-1.0) with BS170 field-effect transistor amplifier:

| Reporter                       | Firmware version | TX frequency | PA bias | Used antenna                 | SNR | Drift | Max distance to receiver  |
|--------------------------------|------------------|--------------|---------|------------------------------|-----|-------|---------------------------|
| [KD9MXZ](mailto:e.moe@rcn.com) | 1.1              | 14.0971 MHz  | 2.610V  | [PackTenna Mini Random Wire] | -28 | 0     | 4618 km                   |                          |

[Windcamp Gipsy]: https://www.windcamp.cn/productinfo/372468.html
[PackTenna Mini Random Wire]: https://www.packtenna.com/store/p1/PackTenna_Mini_Random_Wire_Antenna_%289%3A1_UNUN%29.html#/