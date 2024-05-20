#include <JTEncode.h>
#include <si5351.h>
#include <TimeLib.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>

#define FIRMWARE_VERSION 1.0

//******************************************************************
//                      WSPR configuration
//******************************************************************
// WSPR protocol configuration
#define WSPR_TONE_SPACING          146
#define WSPR_DELAY                 683

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

// WSPR message parameters
#define WSPR_CALL                 "XX0YYY"
#define WSPR_DBM                   23

char WSPR_QTH_LOCATOR[5];

//******************************************************************
//                      Hardware defines
//******************************************************************
#define TX_LED_PIN                 8
#define POWER_ON_LED_PIN           10
#define SI5351_CAL_FACTOR          92000
#define SERIAL_PORT_BAUDRATE       115200

#define GPS_RX_PIN                 3
#define GPS_TX_PIN                 4
#define GPS_BAUDRATE               9600
#define GPS_STATUS_LED_PIN         9
#define GPS_INIT_MAX_TIME          5000
#define GPS_SYNC_ATTEMPTS          10
#define GPS_SYNC_DELAY             30000

//******************************************************************
//                      Global variables
//******************************************************************
uint8_t tx_buffer[255];
Si5351 si5351;
TinyGPSPlus gps;

// Serial connection to the GPS module
SoftwareSerial gpsSerial{GPS_RX_PIN, GPS_TX_PIN};

void(* resetHardware) (void) = 0;

//******************************************************************
//                      Function Prototypes
//******************************************************************
void initializeLEDs();
void initializeGPS();
void initializeSI5351();
void synchronizeGPSData();
bool trySyncGPSData();
void setQTHLocator();
void encodeWSPRMessage();
void transmitWSPRMessage();
void printCurrentDateTime();
void printCurrentLocation();
void printTransmissionDetails();
void printWSPRConfiguration();

//******************************************************************
//                      Function Definitions
//******************************************************************

void initializeLEDs()
{  
    pinMode(TX_LED_PIN, OUTPUT);
    digitalWrite(TX_LED_PIN, LOW);

    pinMode(POWER_ON_LED_PIN, OUTPUT);
    digitalWrite(POWER_ON_LED_PIN, HIGH);
    
    pinMode(GPS_STATUS_LED_PIN, OUTPUT);
    digitalWrite(GPS_STATUS_LED_PIN, LOW);
}

void initializeGPS()
{
    Serial.println(F("- GPS initialization -"));
    
    gpsSerial.begin(GPS_BAUDRATE);

    Serial.print(F("- Getting data from GPS "));
    
    const unsigned long startTime{millis()};
    while (!gpsSerial.available() && millis() <= startTime + GPS_INIT_MAX_TIME)
    {
        delay(600);
        Serial.print(F("."));
    }

    if (gpsSerial.available())
    {
        gps.encode(gpsSerial.read());
        Serial.println(F("\n- GPS successfully initialized! -"));
    }
    else
    {
        Serial.println(F("\n- No GPS detected: check wiring! -"));
        delay(1000);
        resetHardware();
    }
}

void initializeSI5351()
{
    Serial.println(F("- SI5351 initialization -"));
    si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);
    si5351.set_correction(SI5351_CAL_FACTOR, SI5351_PLL_INPUT_XO);
    // Set CLK0 as WSPR TX OUT
    si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_6MA);
    si5351.output_enable(SI5351_CLK0, 0);
    Serial.println(F("- SI5351 successfully initialized! -"));
}

void synchronizeGPSData()
{
    Serial.println(F("- GPS data sychronization -"));
    
    uint8_t syncAttemps{0};
    bool dataSynchronized{trySyncGPSData()};
    while (dataSynchronized == false && syncAttemps < GPS_SYNC_ATTEMPTS)
    {
        delay(GPS_SYNC_DELAY);
        dataSynchronized = trySyncGPSData();
        ++syncAttemps;
    }

    if (dataSynchronized)
    {
        Serial.print(F("- Date & time synchronized by GPS: "));
        printCurrentDateTime();
        Serial.println(F(" -"));
        Serial.print(F("- Location synchronized by GPS: "));
        printCurrentLocation();
        Serial.println(F(" -"));
        Serial.print(F("- QTH locator successfully calculated: "));
        Serial.print(WSPR_QTH_LOCATOR);
        Serial.println(F(" -"));
    }
    else
    {   
        Serial.println(F("- GPS data synchronization not available! -"));
        Serial.println(F("- Transmitting a WSPR message without time & location synchronization is impossible! -"));
        Serial.println(F("- Check your GPS antenna and try again! -"));
        delay(1000);
        resetHardware();
    }
}

bool trySyncGPSData()
{ 
    while (gpsSerial.available())
        gps.encode(gpsSerial.read());

    if (gps.time.isValid() && gps.date.isValid() && gps.location.isValid()){
        setTime(gps.time.hour(), gps.time.minute(), gps.time.second(), gps.date.day(), gps.date.month(), gps.date.year());
        setQTHLocator();
        digitalWrite(GPS_STATUS_LED_PIN, HIGH);
        return true;
    }
    
    return false; 
}

void setQTHLocator() {
    float latitude{gps.location.lat() + 90.0};
    float longitude{gps.location.lng() + 180.0};

    WSPR_QTH_LOCATOR[0] = 'A' + (longitude / 20);
    WSPR_QTH_LOCATOR[1] = 'A' + (latitude / 10);

    WSPR_QTH_LOCATOR[2] = '0' + (int)(longitude / 2) % 10;
    WSPR_QTH_LOCATOR[3] = '0' + (int)(latitude) % 10;

    WSPR_QTH_LOCATOR[4] = '\0';
}

void encodeWSPRMessage()
{
    memset(tx_buffer, 0, 255);
    
    JTEncode jtencode;
    jtencode.wspr_encode(WSPR_CALL, WSPR_QTH_LOCATOR, WSPR_DBM, tx_buffer);
}

void transmittWsprMessage()
{
    // Reset the tone to the base frequency and turn on the output
    Serial.println(F("- TX ON - STARTING WSPR MESSAGE TRANSMISSION -"));

    digitalWrite(TX_LED_PIN, HIGH);
    
    si5351.output_enable(SI5351_CLK0, 1);
    
    for(uint8_t i{0}; i < WSPR_SYMBOL_COUNT; ++i)
    {
      si5351.set_freq((WSPR_DEFAULT_FREQ * 100) + (tx_buffer[i] * WSPR_TONE_SPACING), SI5351_CLK0);
      delay(WSPR_DELAY);
    }

    // Turn off the output
    si5351.output_enable(SI5351_CLK0, 0);

    Serial.println(F("- TX OFF - END OF WSPR MESSAGE TRANSMISSION -"));
    digitalWrite(TX_LED_PIN, LOW);
}

void printCurrentDateTime()
{
    Serial.print(year());
    Serial.print(F("-"));
    Serial.print(month());
    Serial.print(F("-"));
    Serial.print(day());
    Serial.print(F(" "));
    Serial.print(hour());
    Serial.print(F(":"));
    Serial.print(minute());
    Serial.print(F(":"));
    Serial.print(second());
}

void printCurrentLocation()
{
    Serial.print(gps.location.lat());
    Serial.print(F(", "));
    Serial.print(gps.location.lng());
}

void printTransmissionDetails() {
    Serial.print(F("- Start of transmission time: "));
    printCurrentDateTime();
    Serial.println(F(" -"));
    Serial.print(F("- WSPR message: "));
    Serial.print(WSPR_CALL);
    Serial.print(F(" "));
    Serial.print(WSPR_QTH_LOCATOR);
    Serial.print(F(" "));
    Serial.print(WSPR_DBM);
    Serial.println(F(" -"));
}

void printWSPRConfiguration() {
    Serial.println(F("**********************************************"));
    Serial.println(F("[ WSPR BEACON ]"));
    Serial.print(F("- Firmware version: "));
    Serial.print(FIRMWARE_VERSION);
    Serial.println(F(" -"));
    Serial.print(F("- Working frequency: "));
    Serial.print(WSPR_DEFAULT_FREQ / 1000000.0);
    Serial.println(F(" MHz -"));
    Serial.println(F("**********************************************"));
}

void setup()
{
    initializeLEDs();

    Serial.begin(SERIAL_PORT_BAUDRATE); 
    while (!Serial);

    printWSPRConfiguration();
    initializeSI5351();
    initializeGPS();
    synchronizeGPSData();
    setQTHLocator();

    Serial.println(F("**********************************************"));
    Serial.println(F("- Entering WSPR TX loop..."));
    Serial.println(F("**********************************************"));

    encodeWSPRMessage();
}

void loop()
{
    if(const timeStatus_t currentTimeStatus{timeStatus()}; 
      currentTimeStatus == timeSet && minute() % 2 == 0 && second() == 0)
    {
        printTransmissionDetails();
        transmittWsprMessage();
        Serial.println(F("**********************************************"));
    }
    else if (currentTimeStatus != timeSet)
    {
        synchronizeGPSData();
    }
}
