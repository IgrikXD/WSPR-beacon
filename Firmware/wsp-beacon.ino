#include <JTEncode.h>
#include <si5351.h>
#include <TimeLib.h>

#include <TinyGPSPlus.h>
#include <SoftwareSerial.h>

//******************************************************************
//                      WSPR configuration
//******************************************************************
// WSPR protocol configuration
#define WSPR_TONE_SPACING          146
#define WSPR_DELAY                 683

// WSPR center frequency in Hz
// #define WSPR_DEFAULT_FREQ       1838100UL   // 1.8381 MHz
// #define WSPR_DEFAULT_FREQ       3594100UL   // 3.5941 MHz
// #define WSPR_DEFAULT_FREQ       5288700UL   // 5.2887 MHz
// #define WSPR_DEFAULT_FREQ       7040100UL   // 7.0401 MHz
// #define WSPR_DEFAULT_FREQ       10140200UL  // 10.1402 MHz
// #define WSPR_DEFAULT_FREQ       14097100UL  // 14.0971 MHz
// #define WSPR_DEFAULT_FREQ       18106100UL  // 18.1061 MHz
// #define WSPR_DEFAULT_FREQ       21096100UL  // 21.0961 MHz
// #define WSPR_DEFAULT_FREQ       24926100UL  // 24.9261 MHz
#define WSPR_DEFAULT_FREQ       28126100UL  // 28.1261 MHz
// #define WSPR_DEFAULT_FREQ       50294500UL  // 50.2945 MHz

// WSPR message parameters
#define WSPR_CALL                 "XX0YYY"
#define WSPR_LOC                  "XX00"
#define WSPR_DBM                   10
//******************************************************************


//******************************************************************
//                      Hardware defines
//******************************************************************
#define TX_LED_PIN                 8
#define POWER_ON_LED_PIN           10
#define SI5351_CAL_FACTOR          92000
#define SERIAL_PORT_BAUDRATE       115200
#define INIT_MAX_TIME              10000

// GPS module parameters
#define GPS_RX_PIN                 3
#define GPS_TX_PIN                 4
#define GPS_BAUDRATE               9600
#define GPS_STATUS_LED_PIN         9
//******************************************************************

//******************************************************************
//                      Global variables
//******************************************************************
uint8_t tx_buffer[255];
bool warmup{false};
Si5351 si5351;
TinyGPSPlus gps;

// The serial connection to the GPS module
SoftwareSerial gpsSerial{GPS_RX_PIN, GPS_TX_PIN};

//******************************************************************

// Loop through the string, transmitting one character at a time.
void transmittWsprMessage()
{
    // Reset the tone to the base frequency and turn on the output
    Serial.println(F("- TX ON - STARTING WSPR MESSAGE TRANSMISSION -"));

    digitalWrite(TX_LED_PIN, LOW);
    
    si5351.output_enable(SI5351_CLK0, 1);
    
    for(uint8_t i{0}; i < WSPR_SYMBOL_COUNT; ++i)
    {
      si5351.set_freq((WSPR_DEFAULT_FREQ * 100) + (tx_buffer[i] * WSPR_TONE_SPACING), SI5351_CLK0);
      delay(WSPR_DELAY);
    }

    // Turn off the output
    si5351.output_enable(SI5351_CLK0, 0);

    Serial.println(F("- TX OFF - END OF WSPR MESSAGE TRANSMISSION -"));
    digitalWrite(TX_LED_PIN, HIGH);
}

void setWsprTxBuffer()
{
    // Clear out the transmit buffer
    memset(tx_buffer, 0, 255);
    
    JTEncode jtencode;
    jtencode.wspr_encode(WSPR_CALL, WSPR_LOC, WSPR_DBM, tx_buffer);
}

static void ledInit()
{
    Serial.println(F("- LED initialization -"));
    pinMode(TX_LED_PIN, OUTPUT);
    pinMode(POWER_ON_LED_PIN, OUTPUT);
    pinMode(GPS_STATUS_LED_PIN, OUTPUT);
    Serial.println(F("- LED successfully initialized! -"));
}

static void gpsInit()
{
    Serial.println(F("- GPS initialization -"));
    
    gpsSerial.begin(GPS_BAUDRATE);

    Serial.print(F("- Getting data from GPS "));
    
    const auto startTime{millis()};
    while (!gpsSerial.available() && millis() <= startTime + INIT_MAX_TIME)
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
    }
}

static void si5351Init()
{
    Serial.println(F("- SI5351 initialization -"));
    si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);
    si5351.set_correction(SI5351_CAL_FACTOR, SI5351_PLL_INPUT_XO);
    // Set CLK0 as WSPR TX output
    si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_8MA); // Set for max power if desired
    si5351.output_enable(SI5351_CLK0, 0); // Disable the clock initially
    Serial.println(F("- SI5351 successfully initialized! -"));
}

static bool gpsDateTimeSync()
{ 
    while (gpsSerial.available())
        gps.encode(gpsSerial.read());

    if (gps.time.isValid() && gps.date.isValid() && gps.date.year() > 2000){
        setTime(gps.time.hour(), gps.time.minute(), gps.time.second(), gps.date.day(), gps.date.month(), gps.date.year());
        return true;
    }
    
    return false; 
}

String currentDateTime()
{
    const auto& currentTime{now()};

    return {String(year(currentTime)) + "-" 
           + String(month(currentTime)) + "-"
           + String(day(currentTime)) + " "
           + String(hour(currentTime)) + ":"
           + String(minute(currentTime)) + ":" 
           + String(second(currentTime))};
}

time_t dateTimeSyncronization()
{
    Serial.println(F("- Date & time sychronization -"));
    
    uint8_t syncAttemps{0};
    while (!gpsDateTimeSync() && syncAttemps < 10)
    {
        delay(10000);
        ++syncAttemps;
    }

    if (timeStatus() == timeSet)
    {
        Serial.print(F("- Date & time synchronized by GPS: "));
        Serial.print(currentDateTime());
        Serial.println(F(" -"));
    }
    else
    {   
        Serial.println(F("- GPS time sync not available! -"));
        Serial.println(F("- Transmitting a WSPR message without time synchronization is impossible! -"));
        Serial.println(F("- Check your GPS and try again! -"));
        delay(1000);
        exit(0);
    }

    return now();
}

void setup()
{
    // Serial port initialization
    Serial.begin(SERIAL_PORT_BAUDRATE); 
    while (!Serial);

    // Welcome message & working frequency info
    Serial.println(F("**********************************************"));
    Serial.println(F("[ WSPR BEACON ]"));
    Serial.print(F("- Working frequency: "));
    Serial.print(WSPR_DEFAULT_FREQ / 1000000.0);
    Serial.println(F(" MHz -"));
    Serial.println(F("**********************************************"));

    // LED initialization
    ledInit();

    // GPS module initialization
    gpsInit();
  
    // SI5351 IC initialization
    si5351Init();

    dateTimeSyncronization();

    Serial.println(F("**********************************************"));
    Serial.println(F("- Entering WSPR TX loop..."));
    digitalWrite(TX_LED_PIN, HIGH);
    Serial.println(F("**********************************************"));

    // Encode the message in the transmit buffer
    // This is RAM intensive and should be done separately from other subroutines
    setWsprTxBuffer();
}

void loop()
{
    if((minute() + 1) % 4 == 0 && second() == 30 && !warmup)
    {
        warmup = true;
        Serial.println(F("- Radio module warm up started! -"));
        si5351.set_freq(WSPR_DEFAULT_FREQ * 100, SI5351_CLK0);
        si5351.output_enable(SI5351_CLK0, 1);
    }

    if(minute() % 4 == 0 && second() == 0)
    {
        warmup = false;
        Serial.print(F("- Start of transmission time: "));
        Serial.print(currentDateTime());
        Serial.println(F(" -"));

        Serial.print(F("- WSPR message: "));
        Serial.print(WSPR_CALL);
        Serial.print(F(" "));
        Serial.print(WSPR_LOC);
        Serial.print(F(" "));
        Serial.print(WSPR_DBM);
        Serial.println(F(" -"));

        transmittWsprMessage();

        Serial.println(F("\n**********************************************"));
    }
}
