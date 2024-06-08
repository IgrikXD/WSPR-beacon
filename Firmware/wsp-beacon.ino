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
#define WSPR_MESSAGE_BUFFER_SIZE   255

// WSPR center frequency in Hz
// #define WSPR_DEFAULT_FREQ       137500ULL    // 0.1375 MHz - 2200m
// #define WSPR_DEFAULT_FREQ       475700ULL    // 0.4757 MHz - 600m
// #define WSPR_DEFAULT_FREQ       1838100ULL   // 1.8381 MHz - 160m
// #define WSPR_DEFAULT_FREQ       3570100ULL   // 3.5701 MHz - 80m
// #define WSPR_DEFAULT_FREQ       5288700ULL   // 5.2887 MHz - 60m
// #define WSPR_DEFAULT_FREQ       7040100ULL   // 7.0401 MHz - 40m
// #define WSPR_DEFAULT_FREQ       10140200ULL  // 10.1402 MHz - 30m
// #define WSPR_DEFAULT_FREQ       14097100ULL  // 14.0971 MHz - 20m
// #define WSPR_DEFAULT_FREQ       18106100ULL  // 18.1061 MHz - 17m
// #define WSPR_DEFAULT_FREQ       21096100ULL  // 21.0961 MHz - 15m
// #define WSPR_DEFAULT_FREQ       24926100ULL  // 24.9261 MHz - 12m
#define WSPR_DEFAULT_FREQ       28126100ULL  // 28.1261 MHz - 10m
// #define WSPR_DEFAULT_FREQ       50294500ULL  // 50.2945 MHz - 6m
// #define WSPR_DEFAULT_FREQ       144490000ULL  // 144.4900 MHz - 2m

// WSPR message parameters
#define WSPR_CALL                 "XX0YYY"
#define WSPR_DBM                   23

char WSPR_QTH_LOCATOR[5];

//******************************************************************
//                      Hardware defines
//******************************************************************
#define TX_LED_PIN                 8
#define POWER_ON_LED_PIN           10
#define SERIAL_PORT_BAUDRATE       115200
#define RESET_DELAY                1000

#define SI5351_CAL_FACTOR          2000
#define SI5351_I2C_ADDRESS         0x60

#define GPS_RX_PIN                 4
#define GPS_TX_PIN                 3
#define GPS_BAUDRATE               9600
#define GPS_SERIAL_READ_DURATION   1000
#define GPS_STATUS_LED_PIN         9
#define GPS_INIT_MAX_TIME          5000
#define GPS_INIT_DELAY             500
#define GPS_SYNC_ATTEMPTS          10
#define GPS_SYNC_DELAY             10000

//******************************************************************
//                      Global variables
//******************************************************************
uint8_t tx_buffer[WSPR_MESSAGE_BUFFER_SIZE];
Si5351 si5351(SI5351_I2C_ADDRESS);
TinyGPSPlus gps;

void(* resetHardware) (void) = 0;

//******************************************************************
//                      Function Prototypes
//******************************************************************
void initializeLEDs();
void initializeGPSSerialConnection();
void initializeSI5351();
void synchronizeGPSData();
bool trySyncGPSData();
void setQTHLocator();
void encodeWSPRMessage();
void transmitWSPRMessage();
void printCurrentDateTime();
void printCurrentLocation();
void printDelimiter();
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

void initializeGPSSerialConnection(SoftwareSerial& gpsSerial)
{
    Serial.println(F("- GPS initialization -"));
    
    gpsSerial.begin(GPS_BAUDRATE);
    
    const unsigned long startTime{millis()};
    while (gpsSerial.available() == false && millis() <= startTime + GPS_INIT_MAX_TIME)
    {
        delay(GPS_INIT_DELAY);
    }

    if (gpsSerial.available())
    {
        Serial.println(F("- GPS successfully initialized! -"));
    }
    else
    {
        Serial.println(F("- GPS initialization error! -"));
        delay(RESET_DELAY);
        resetHardware();
    }
}

void initializeSI5351()
{
    Serial.println(F("- SI5351 initialization -"));
    if (si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, SI5351_CAL_FACTOR))
    {
        Serial.println(F("- SI5351 successfully initialized! -"));
        // Set CLK0 as TX OUT
        si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_6MA);
        si5351.output_enable(SI5351_CLK0, 0);
    }
    else
    {
        Serial.println(F("- SI5351 initialization error! -"));
        Serial.print(F("- Ensure that the SI5351 has an I2C address 0x"));
        Serial.print(SI5351_I2C_ADDRESS, HEX);
        Serial.println(F(" -"));
        delay(RESET_DELAY);
        resetHardware();
    }

}

void synchronizeGPSData()
{
    SoftwareSerial gpsSerial{GPS_RX_PIN, GPS_TX_PIN};

    initializeGPSSerialConnection(gpsSerial);

    Serial.println(F("- GPS data sync -"));
    
    uint8_t syncAttemps{1};
    bool dataSynchronized{trySyncGPSData(gpsSerial)};
    while (dataSynchronized == false && syncAttemps < GPS_SYNC_ATTEMPTS)
    {
        Serial.print(F("- Sync attempt "));
        Serial.print(syncAttemps);
        Serial.println(F(" failed! -"));
        Serial.println(F("- Waiting for the next sync attempt... -"));
        delay(GPS_SYNC_DELAY);
        dataSynchronized = trySyncGPSData(gpsSerial);
        ++syncAttemps;
    }

    if (dataSynchronized)
    {
        Serial.print(F("- Date & time (GMT) synchronized by GPS: "));
        printCurrentDateTime();
        Serial.println(F(" -"));
        Serial.print(F("- Location synchronized by GPS: "));
        printCurrentLocation();
        Serial.println(F(" -"));
        Serial.print(F("- QTH locator: "));
        Serial.print(WSPR_QTH_LOCATOR);
        Serial.println(F(" -"));
    }
    else
    {   
        Serial.println(F("- GPS data sync not available! -"));
        Serial.println(F("- Transmitting a WSPR message without time & location sync is impossible! -"));
        Serial.println(F("- Check your GPS antenna and try again! -"));
        delay(RESET_DELAY);
        resetHardware();
    }
}

bool trySyncGPSData(SoftwareSerial& gpsSerial)
{ 
    const unsigned long startTime{millis()};
    while (millis() - startTime < GPS_SERIAL_READ_DURATION) 
    {
        while (gpsSerial.available())
            gps.encode(gpsSerial.read());
    }

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

    WSPR_QTH_LOCATOR[2] = '0' + (uint8_t)(longitude / 2) % 10;
    WSPR_QTH_LOCATOR[3] = '0' + (uint8_t)(latitude) % 10;

    WSPR_QTH_LOCATOR[4] = '\0';
}

void encodeWSPRMessage()
{
    memset(tx_buffer, 0, WSPR_MESSAGE_BUFFER_SIZE);
    
    JTEncode jtencode;
    jtencode.wspr_encode(WSPR_CALL, WSPR_QTH_LOCATOR, WSPR_DBM, tx_buffer);
}

void transmittWsprMessage()
{
    Serial.println(F("- WSPR TX ON -"));

    digitalWrite(TX_LED_PIN, HIGH);
  
    // WSPR message transmission at each function call is performed on a randomly selected 
    // frequency within the range of +/- 100 Hz from the center frequency.
    const unsigned long transmissionFrequency{WSPR_DEFAULT_FREQ + random(-100, 101)};

    Serial.print(F("- Transmisson frequency: "));
    Serial.print(transmissionFrequency / 1000000.0, 6);
    Serial.println(F(" MHz -"));

    si5351.output_enable(SI5351_CLK0, 1);

    for(uint8_t i{0}; i < WSPR_SYMBOL_COUNT; ++i)
    {
      si5351.set_freq(transmissionFrequency * 100ULL + (tx_buffer[i] * WSPR_TONE_SPACING), SI5351_CLK0);
      delay(WSPR_DELAY);
    }

    si5351.output_enable(SI5351_CLK0, 0);

    Serial.println(F("- WSPR TX OFF -"));
    digitalWrite(TX_LED_PIN, LOW);
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

void printCurrentLocation()
{
    Serial.print(gps.location.lat(), 4);
    Serial.print(F(", "));
    Serial.print(gps.location.lng(), 4);
}

void printDelimiter()
{
    Serial.println(F("********************************************"));
}

void printTransmissionDetails() {
    Serial.print(F("- Start of transmission time (GMT): "));
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
    printDelimiter();
    Serial.println(F("[ WSPR BEACON ]"));
    Serial.print(F("- Firmware version: "));
    Serial.print(FIRMWARE_VERSION);
    Serial.println(F(" -"));
    Serial.print(F("- Working frequency: "));
    Serial.print(WSPR_DEFAULT_FREQ / 1000000.0, 6);
    Serial.println(F(" MHz -"));
    printDelimiter();
}

void setup()
{
    initializeLEDs();

    Serial.begin(SERIAL_PORT_BAUDRATE); 
    while (!Serial);

    printWSPRConfiguration();
    initializeSI5351();
    synchronizeGPSData();

    printDelimiter();
    Serial.println(F("- Entering WSPR TX loop..."));
    printDelimiter();

    encodeWSPRMessage();
    randomSeed(millis());
}

void loop()
{
    if(second() == 0 && minute() % 2 == 0)
    {
        printTransmissionDetails();
        transmittWsprMessage();
        printDelimiter();
        synchronizeGPSData();
        printDelimiter();
    }
}
