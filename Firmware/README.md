# Firmware instruction

## Select the transmission frequency:
Open Arduino IDE and modify the [_wsp-beacon.ino_](wsp-beacon.ino) file. Uncomment the line with the band on which you want to perform the WSPR message transmission:
```cpp
// WSPR center frequency in Hz
// #define WSPR_DEFAULT_FREQ       137500UL    // 0.1375 MHz - 2200m
// #define WSPR_DEFAULT_FREQ       475700UL    // 0.4757 MHz - 600m
// #define WSPR_DEFAULT_FREQ       1838100UL   // 1.8381 MHz - 160m
// #define WSPR_DEFAULT_FREQ       3570100UL   // 3.5701 MHz - 80m
// #define WSPR_DEFAULT_FREQ       5288700UL   // 5.2887 MHz - 60m
// #define WSPR_DEFAULT_FREQ       7040100UL   // 7.0401 MHz - 40m
// #define WSPR_DEFAULT_FREQ       10140200UL  // 10.1402 MHz - 30m
// #define WSPR_DEFAULT_FREQ       14097100UL  // 14.0971 MHz - 20m
// #define WSPR_DEFAULT_FREQ       18106100UL  // 18.1061 MHz - 17m
// #define WSPR_DEFAULT_FREQ       21096100UL  // 21.0961 MHz - 15m
// #define WSPR_DEFAULT_FREQ       24926100UL  // 24.9261 MHz - 12m
#define WSPR_DEFAULT_FREQ       28126100UL  // 28.1261 MHz - 10m
// #define WSPR_DEFAULT_FREQ       50294500UL  // 50.2945 MHz - 6m
// #define WSPR_DEFAULT_FREQ       144490000UL  // 144.4900 MHz - 2m
```

## Add WSPR message data:
Enter your amateur radio call sign to generate a correct WSPR message:
```cpp
#define WSPR_CALL                 "XX0YYY"
```

## Select the Board:
Go to "_Tools_" -> "_Board_", then select  "_Arduino Nano_".

## Choose the Port:
Connect the device to your computer via USB cable. Then, in the "_Tools_" -> "_Port_" menu, select the corresponding COM port.

## Upload an Firmware:
Click the "_Upload_" button in the Arduino IDE to compile and upload your program to the device.