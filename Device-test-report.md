# WSPR-beacon device test report

This section provides information about the device's performance during long distance WSPR message transmission. Data on transmitted and decoded WSPR messages are taken from the [WSPR Rocks!](http://wspr.rocks/)

For each transmission range, a visualized report with a list of all spots is available. To view the visualization, click on the distance in the "_Max distance to receiver_" column.

> [!NOTE]
>During testing of the device, the antenna used was tuned to the resonant frequency using the NanoVNA vector network analyzer. 
>**Please note that the efficiency of the antenna largely depends on the conditions of its installation.** In addition to tuning the antenna to the minimum SWR value, the quality of the antenna's performance is influenced by the installation height, orientation, the presence of dense urban buildings, thick forests, and electromagnetic interference.

**Power source used:** Mi Power Bank Pro PLM07ZM

### [PCB version 1.0](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-1.0) with BS170 field-effect transistor amplifier:

| Firmware version | Transmission frequency | Used antenna     | SNR | Frequency drift | Max distance to receiver                         |
|------------------|------------------------|------------------|-----|-----------------|--------------------------------------------------|
| 1.0              | 5.2887 MHz             | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.0              | 7.0401 MHz             | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.0              | 10.1402 MHz            | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.0              | 14.0971 MHz            | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 5.2887 MHz             | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 7.0401 MHz             | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 10.1402 MHz            | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 14.0971 MHz            | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |

### [PCB version 2.0](https://github.com/IgrikXD/WSPR-beacon/releases/tag/wspr-beacon-pcb-2.0) with SN74ACT244PWR buffer amplifier:

| Firmware version | Transmission frequency | Used antenna     | SNR | Frequency drift | Max distance to receiver                         |
|------------------|------------------------|------------------|-----|-----------------|--------------------------------------------------|
| 1.1              | 5.2887 MHz             | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 7.0401 MHz             | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 10.1402 MHz            | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |
| 1.1              | 14.0971 MHz            | [Windcamp Gipsy] | 0   | 0               | [0 km](                                        ) |

[Windcamp Gipsy]: https://www.windcamp.cn/productinfo/372468.html