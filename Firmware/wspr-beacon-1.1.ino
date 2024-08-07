#include <JTEncode.h>
#include <si5351.h>
#include <SoftwareSerial.h>
#include <TimeLib.h>
#include <TinyGPS++.h>

#define FIRMWARE_VERSION 1.1

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
// #define WSPR_DEFAULT_FREQ       70092500ULL  // 70.0925 MHz - 4m
// #define WSPR_DEFAULT_FREQ       144490500ULL // 144.4905 MHz - 2m

// WSPR message parameters
#define WSPR_CALL                 "XX0YYY"
#define WSPR_DBM                   23

//******************************************************************
//                      Hardware defines
//******************************************************************
#define TX_LED_PIN                 8
#define POWER_ON_LED_PIN           10

#define SI5351_CAL_FACTOR          2000
#define SI5351_I2C_ADDRESS         0x60

#define GPS_RX_PIN                 4
#define GPS_TX_PIN                 3
#define GPS_BAUDRATE               9600
#define GPS_SERIAL_READ_DURATION   1200
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
uint64_t transmissionFrequency;

void(* resetHardware) (void) = 0;

//******************************************************************
//                      Function prototypes
//******************************************************************
void encodeWSPRMessage(const TinyGPSPlus& gpsDataObj);
void errorLEDIndicationAndReboot();
void initializeGPSSerialConnection(SoftwareSerial& gpsSerial);
void initializeLEDs();
void initializeSI5351();
void setQTHLocator(const TinyGPSPlus& gpsDataObj, char qthLocator[]);
void setTransmissionFrequency();
void synchronizeDateTime(TinyGPSPlus& gpsDataObj);
void transmitWSPRMessage();
bool trySyncGPSData(SoftwareSerial& gpsSerial, TinyGPSPlus& gpsDataObj);

//******************************************************************
//                      Function definitions
//******************************************************************
void encodeWSPRMessage(const TinyGPSPlus& gpsDataObj)
{
    memset(tx_buffer, 0, WSPR_MESSAGE_BUFFER_SIZE);
    
    char qthLocator[5];
    setQTHLocator(gpsDataObj, qthLocator);

    JTEncode jtencode;
    jtencode.wspr_encode(WSPR_CALL, qthLocator, WSPR_DBM, tx_buffer);
}

void errorLEDIndicationAndReboot()
{
    // Turn off all the green LEDs (GPS, ON)
    digitalWrite(POWER_ON_LED_PIN, LOW);
    digitalWrite(GPS_STATUS_LED_PIN, LOW);

    // Flash the red LED (TX) three times
    for (uint8_t i{0}; i < 3; ++i) {
        digitalWrite(TX_LED_PIN, HIGH);
        delay(500);
        digitalWrite(TX_LED_PIN, LOW);
        delay(500);
    }

    resetHardware();
}

void initializeGPSSerialConnection(SoftwareSerial& gpsSerial)
{   
    gpsSerial.begin(GPS_BAUDRATE);
    
    const uint32_t startTime{millis()};
    while (gpsSerial.available() == false && millis() <= startTime + GPS_INIT_MAX_TIME)
        delay(GPS_INIT_DELAY);

    if (gpsSerial.available() == false)
        errorLEDIndicationAndReboot();
}

void initializeLEDs()
{  
    pinMode(TX_LED_PIN, OUTPUT);
    digitalWrite(TX_LED_PIN, LOW);

    pinMode(POWER_ON_LED_PIN, OUTPUT);
    digitalWrite(POWER_ON_LED_PIN, HIGH);
    
    pinMode(GPS_STATUS_LED_PIN, OUTPUT);
    digitalWrite(GPS_STATUS_LED_PIN, LOW);
}

void initializeSI5351()
{
    if (si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, SI5351_CAL_FACTOR))
        // Set CLK0 as TX OUT
        si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_8MA);
    else
        errorLEDIndicationAndReboot();
}

void setQTHLocator(const TinyGPSPlus& gpsDataObj, char qthLocator[]) {
    const float latitude{gpsDataObj.location.lat() + 90.0};
    const float longitude{gpsDataObj.location.lng() + 180.0};

    qthLocator[0] = 'A' + (longitude / 20);
    qthLocator[1] = 'A' + (latitude / 10);

    qthLocator[2] = '0' + (uint8_t)(longitude / 2) % 10;
    qthLocator[3] = '0' + (uint8_t)(latitude) % 10;

    qthLocator[4] = '\0';
}

void setTransmissionFrequency()
{
    // WSPR message transmission at each transmitWSPRMessage() function call is performed on 
    // a randomly selected frequency within the range of +/- 100 Hz from the center frequency
    transmissionFrequency = (WSPR_DEFAULT_FREQ + random(-100, 101)) * 100ULL;
}

void synchronizeDateTime(TinyGPSPlus& gpsDataObj)
{
    SoftwareSerial gpsSerial{GPS_RX_PIN, GPS_TX_PIN};

    initializeGPSSerialConnection(gpsSerial);
    
    uint8_t syncAttemps{1};
    bool dataSynchronized{trySyncGPSData(gpsSerial, gpsDataObj)};
    while (dataSynchronized == false && syncAttemps < GPS_SYNC_ATTEMPTS)
    {
        delay(GPS_SYNC_DELAY);
        dataSynchronized = trySyncGPSData(gpsSerial, gpsDataObj);
        ++syncAttemps;
    }

    if (dataSynchronized == false)
        errorLEDIndicationAndReboot();
}

void transmitWSPRMessage()
{
    digitalWrite(TX_LED_PIN, HIGH);

    si5351.output_enable(SI5351_CLK0, 1);

    for(uint8_t i{0}; i < WSPR_SYMBOL_COUNT; ++i)
    {
        si5351.set_freq(transmissionFrequency + (tx_buffer[i] * WSPR_TONE_SPACING), SI5351_CLK0);
        delay(WSPR_DELAY);
    }

    si5351.output_enable(SI5351_CLK0, 0);

    digitalWrite(TX_LED_PIN, LOW);
}

bool trySyncGPSData(SoftwareSerial& gpsSerial, TinyGPSPlus& gpsDataObj)
{ 
    const uint32_t startTime{millis()};
    while (millis() - startTime < GPS_SERIAL_READ_DURATION) 
    {
        while (gpsSerial.available())
            gpsDataObj.encode(gpsSerial.read());
    }

    if (gpsDataObj.time.isValid() && gpsDataObj.date.isValid() && gpsDataObj.location.isValid()){
        setTime(gpsDataObj.time.hour(), gpsDataObj.time.minute(), gpsDataObj.time.second(), 
                gpsDataObj.date.day(), gpsDataObj.date.month(), gpsDataObj.date.year());

        digitalWrite(GPS_STATUS_LED_PIN, HIGH);
        return true;
    }
    
    digitalWrite(GPS_STATUS_LED_PIN, LOW);
    return false; 
}

//******************************************************************
//                      Main firmware code
//******************************************************************
void setup()
{
    initializeLEDs();
    initializeSI5351();

    TinyGPSPlus gpsDataObj;
    synchronizeDateTime(gpsDataObj);

    // RAM-intensive operation, generate WSPR message only once, at device startup
    encodeWSPRMessage(gpsDataObj);
    
    // Initialize the random number generator with a seed based on the current time
    randomSeed(millis());
    // Setting the random transmission frequency within the range of +/- 100 Hz from 
    // the center operating frequency
    setTransmissionFrequency();
}

void loop()
{
    // Transmission of a WSPR message every even minute (00:00, 00:02, 00:04, ...)
    if(second() == 0 && minute() % 2 == 0)
    {
        transmitWSPRMessage();
        
        // Time synchronization based on current GPS data for a new transmission cycle
        TinyGPSPlus gpsDataObj;
        synchronizeDateTime(gpsDataObj);
        
        // Set a new, random transmission frequency
        setTransmissionFrequency();
    }
}
