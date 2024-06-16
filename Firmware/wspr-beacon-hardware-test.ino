#include <si5351.h>
#include <SoftwareSerial.h>
#include <TimeLib.h>
#include <TinyGPS++.h>

//******************************************************************
//                      Hardware defines
//******************************************************************
#define SERIAL_PORT_BAUDRATE       115200

#define SI5351_I2C_ADDRESS         0x60

#define GPS_RX_PIN                 4
#define GPS_TX_PIN                 3
#define GPS_BAUDRATE               9600
#define GPS_SERIAL_READ_DURATION   1200
#define GPS_INIT_MAX_TIME          5000
#define GPS_INIT_DELAY             500
#define GPS_SYNC_ATTEMPTS          10
#define GPS_SYNC_DELAY             10000

//******************************************************************
//                      Function Prototypes
//******************************************************************
bool initializeGPSSerialConnection(SoftwareSerial& gpsSerial);
void printCurrentDateTime();
void printDelimiter();
bool tryInitSI5351();
bool trySyncDateTimeByGPS(TinyGPSPlus& gpsDataObj);
bool trySyncGPSData(SoftwareSerial& gpsSerial, TinyGPSPlus& gpsDataObj);

//******************************************************************
//                      Function Definitions
//******************************************************************
bool initializeGPSSerialConnection(SoftwareSerial& gpsSerial)
{   
    Serial.println("- Establishing a serial connection to the GPS module ... -");

    gpsSerial.begin(GPS_BAUDRATE);
    
    const uint32_t startTime{millis()};
    while (gpsSerial.available() == false && millis() <= startTime + GPS_INIT_MAX_TIME)
        delay(GPS_INIT_DELAY);

    if (gpsSerial.available())
    {
        Serial.println(F("- Serial connection to GPS module successfully established! -"));
        printDelimiter();
        return true;  
    }
    
    Serial.println(F("- Establishing a serial connection to the GPS module failed! -"));
    Serial.println(F("- Check the pinout of the GPS module used! -"));
    printDelimiter();
    return false;
}

void printCurrentDateTime()
{
    Serial.print(day());
    Serial.print(F("/"));
    Serial.print(month());
    Serial.print(F("/"));
    Serial.print(year());
    Serial.print(F(" "));
    Serial.print(hour());
    Serial.print(F(":"));
    Serial.print(minute());
    Serial.print(F(":"));
    Serial.print(second());
}

void printDelimiter()
{
    Serial.println(F("***************************************************"));
}

bool tryInitSI5351()
{
    Si5351 si5351(SI5351_I2C_ADDRESS);

    if (si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0))
    {
        Serial.print(F("- SI5351 successfully initialized at address 0x"));
        Serial.print(SI5351_I2C_ADDRESS, HEX);
        Serial.println(F("! -"));
        printDelimiter();
        return true;
    }
    else
    {
        Serial.println(F("- SI5351 initialization error! -"));
        Serial.print(F("- Ensure that the SI5351 has an I2C address 0x"));
        Serial.print(SI5351_I2C_ADDRESS, HEX);
        Serial.println(F(" -"));
        printDelimiter();
        return false;
    }
}

bool trySyncDateTimeByGPS()
{
    SoftwareSerial gpsSerial{GPS_RX_PIN, GPS_TX_PIN};

    if (initializeGPSSerialConnection(gpsSerial) == false)
        return false;

    Serial.println(F("- GPS data synchronization test ... -"));
    
    TinyGPSPlus gpsDataObj;
    uint8_t syncAttemps{1};
    bool dataSynchronized{trySyncGPSData(gpsSerial, gpsDataObj)};
    while (dataSynchronized == false && syncAttemps < GPS_SYNC_ATTEMPTS)
    {
        Serial.print(F("- GPS data sync attempt "));
        Serial.print(syncAttemps);
        Serial.println(F(" failed! -"));
        Serial.println(F("- Waiting for the next sync attempt ... -"));
        delay(GPS_SYNC_DELAY);
        dataSynchronized = trySyncGPSData(gpsSerial, gpsDataObj);
        ++syncAttemps;
    }

    if (dataSynchronized)
    {
        Serial.print(F("- Date & time (GMT) synchronized by GPS: "));
        printCurrentDateTime();
        Serial.println(F(" -"));
        Serial.print(F("- Location synchronized by GPS: "));
        Serial.print(gpsDataObj.location.lat(), 4);
        Serial.print(F(", "));
        Serial.print(gpsDataObj.location.lng(), 4);
        Serial.println(F(" -"));
        printDelimiter();
        return true;
    }
    else
    {   
        Serial.println(F("- GPS data synchronization not available! -"));
        Serial.println(F("- Check your GPS antenna and try again! -"));
        Serial.println(F("- Make sure you are using an active GPS antenna! -"));
        Serial.println(F("- Make sure that the \"GPS ANT\" port has the necessary antenna power supply voltage! -"));
        printDelimiter();
        return false;
    }
}

bool trySyncGPSData(SoftwareSerial& gpsSerial, TinyGPSPlus& gpsDataObj)
{ 
    const uint32_t startTime{millis()};
    while (millis() - startTime < GPS_SERIAL_READ_DURATION) 
    {
        while (gpsSerial.available())
            gpsDataObj.encode(gpsSerial.read());
    }

    if (gpsDataObj.time.isValid() && gpsDataObj.date.isValid() && gpsDataObj.location.isValid())
        return true;
    
    return false; 
}

//******************************************************************
//              Main firmware code for hardware testing
//******************************************************************
void setup()
{
    Serial.begin(SERIAL_PORT_BAUDRATE); 
    while (!Serial);

    printDelimiter();
    Serial.println(F("[ WSPR BEACON HARDWARE TEST ]: Starting ..."));
    printDelimiter();

    if (tryInitSI5351() && trySyncDateTimeByGPS())
        Serial.println(F("[ WSPR BEACON HARDWARE TEST ]: Success!"));
    else
        Serial.println(F("[ WSPR BEACON HARDWARE TEST ]: Fail!"));
    printDelimiter();
}

void loop() { }