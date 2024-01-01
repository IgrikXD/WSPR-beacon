# wspr-beacon

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


Used:
https://antrak.org.tr/blog/esp-wspr-simple-and-inexpensive-wspr-transmitter/  
https://github.com/adecarolis/K1FM-WSPR-TX  
https://aa7ee.wordpress.com/2023/02/26/a-little-wspr-beacon-arent-they-all-little/  