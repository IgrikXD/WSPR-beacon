# wspr-beacon

This program is a revised version of the [ESP WSPR](https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/) program.  

**Main changes:** added GPS time synchronization (has priority over NTP synchronization, NTP synchronization is used if GPS time synchronization is not available), changed the detail of displaying status information while the program is running, code refactoring.

## How to use?

To use NTP synchronization, change the following parameters to match the actual data of your Wi-Fi network:
```sh
#define SSID                      "SSID"
#define PASSWORD                  "PASSWORD"
```

Enter your amateur radio call sign, the first 4 characters of your QTH locator and the transmitted power value to generate a correct WSPR message:
```sh
#define WSPR_CALL                 "XX0YYY"
#define WSPR_LOC                  "XX00"
#define WSPR_DBM                   10
```

## Firmware instruction

### Set up Additional Board Manager URLs:
Go to "_File_" -> "_Preferences_." In the "_Additional Boards Manager URLs_" field, add the following URL:
```sh
http://arduino.esp8266.com/stable/package_esp8266com_index.json
```
Click "_OK_" to save the settings.

### Install ESP8266 Packages:
Navigate to "_Tools_" -> "_Board_" -> "_Boards Manager._" In the search bar, type "_ESP8266_" and install the "_ESP8266_" package from the ESP8266 community.

### Select the Board:
Now, in the "_Tools_" -> "_Board_" menu, choose "_NodeMCU 0.9 (ESP-12 Module)_" or the specific ESP8266 board you are using.

### Choose the Port:
Connect the ESP8266 to your computer via USB. Then, in the "_Tools_" -> "_Port_" menu, select the corresponding port.

## Resources:
[ESP WSPR – Simple and Inexpensive WSPR Transmitter - Ankara Telsiz ve Radyo Amatörleri Kulübü Derneği](https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/)  
[K1FM-WSPR-TX - GitHub](https://github.com/adecarolis/K1FM-WSPR-TX)  
[A Little WSPR Beacon (Aren’t They All Little?) – Dave Richards AA7EE](https://aa7ee.wordpress.com/2023/02/26/a-little-wspr-beacon-arent-they-all-little/  )