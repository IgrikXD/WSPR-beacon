# Firmware instruction

## Add WSPR message data:
Open Arduino IDE and modify the _wsp-beacon.ino_ file. Enter your amateur radio call sign, the first 4 characters of your QTH locator and the transmitted power value to generate a correct WSPR message:
```sh
#define WSPR_CALL                 "XX0YYY"
#define WSPR_LOC                  "XX00"
#define WSPR_DBM                   23
```

## Select the Board:
Go to "_Tools_" -> "_Board_", then select  "_Arduino Nano_".

## Choose the Port:
Connect the device to your computer via USB cable. Then, in the "_Tools_" -> "_Port_" menu, select the corresponding COM port.

## Upload an Firmware:
Click the "_Upload_" button in the Arduino IDE to compile and upload your program to the device.