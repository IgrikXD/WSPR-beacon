# WSPR-beacon usage guide

## Device preparation
[Assemble the device](./Assembly-guide.md) and [upload the firmware](./Firmware/). Connect active GPS antenna, antenna for WSPR message transmission and USB-B cable for device power supply.  

> [!NOTE]
>It is recommended to use full-size antennas for a specific transmission range, as their efficiency is significantly superior to that of wideband and compact antennas. Also, it is recommended to use bandpass filters that suppress unwanted signals outside the operating range (the SI5351 emits unwanted harmonics along with the main signal emission at the operating frequency).

## Device usage
The device operates in fully automatic mode. Turn on the device by switching the **_SW1_** toggle switch position. After switching on the device the **_green LED (ON)_** should light up, which means that the device is working correctly and the initialization process has started. 

### Hardware initialization
Initialization of the hardware is performed in the _void setup()_ function and is executed only once, when the device is started.  

By default, the SI5351 is initialized at I2C address 0x60. If no device is detected at this address, an initialization error is indicated by the LED (_the **red LED (TX)** blinks three times_) and the device subsequently restarts. **If you encounter any problems at this stage - make sure that your SI5351 instance really has I2C address 0x60!** If necessary, you can [change the value of the I2C address of the SI5351](https://github.com/IgrikXD/WSPR-beacon/tree/master/Firmware#i2c-address-of-the-si5351) in the firmware source code.

The GPS module used in the device operates using a software-implemented serial port. Initialization of the GPS module starts with checking if any information is available from the GPS receiver on the virtual serial port. If no data is received within "_GPS_INIT_MAX_TIME_" - an GPS module initialization error is indicated by the LED (_the **red LED (TX)** blinks three times_) and the device will be rebooted. 

If the connection is successfully initialized, date and time synchronization is performed based on the data received from the GPS module. The device performs "_GPS_SYNC_ATTEMPTS_" attempts to synchronize GPS data with a delay of "_GPS_SYNC_DELAY_". If all synchronization attempts fail, an GPS data synchronization error is indicated by the LED (_the **red LED (TX)** blinks three times_) and the device is rebooted.  

> [!WARNING]
>The device will not transmit WSPR messages until the time and coordinates are synchronized!  

Successful completion of GPS data synchronization is signaled by a **_green LED (GPS)_**, after which the device proceeds to generate a buffer containing a WSPR message for transmission.

The calculation of your QTH locator is performed once during the device initialization based on current GPS data. The QTH locator is calculated during the execution of the _void encodeWSPRMessage(const TinyGPSPlus& gpsDataObj)_ function using the _void setQTHLocator(const TinyGPSPlus& gpsDataObj, char qthLocator[])_ function and is immediately written to the buffer responsible for forming the transmitted WSPR message. **Subsequently, during the operation of the device, the QTH locator is not updated!**  

### WSPR message transmission
Transmission of WSPR messages is performed in an infinite loop _void loop()_ every even minute (_00:00, 00:02, 00:04, ..._). **Each transmission cycle is executed at a randomly selected frequency within the range of +/- 100 Hz from the center operating frequency.** During the WSPR message transmission, the **_red LED (TX)_** lights up and goes out immediately after the transmission is completed. After completion of the transmission cycle, the device re-synchronizes the time based on the current GPS data values.
