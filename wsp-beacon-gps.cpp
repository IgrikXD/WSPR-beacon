#include <ESP8266WiFi.h>
#include <int.h>
#include <JTEncode.h>
#include <NTPtimeESP.h>
#include <rs_common.h>
#include <si5351.h>
#include <string.h>
#include <TimeLib.h>
#include <WiFiClient.h>

#include <TinyGPS++.h>
#include <SoftwareSerial.h>

#include "Wire.h"

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
#define TX_LED_PIN                 2
#define SI5351_CAL_FACTOR          92000
#define ESP_SERIAL_PORT_BAUDRATE   115200
#define INIT_MAX_TIME              10000

// GPS module parameters
#define GPS_RX_PIN                 12
#define GPS_TX_PIN                 14
#define GPS_BAUDRATE               9600
//******************************************************************


//******************************************************************
//                        WiFi parameters
//******************************************************************
#define SSID                      "SSID"
#define PASSWORD                  "PASSWORD"
//******************************************************************


//******************************************************************
//                          NTP parameters
//******************************************************************
#define NTP_PROVIDER              "time.windows.com"
#define SEND_INTV                 10
#define RECV_TIMEOUT              10
#define TIME_ZONE                 +1.0f
#define MAX_SYNC_ATTEMPTS         10
#define SYNC_DELAY                200
//******************************************************************

template <typename T> inline HardwareSerial& operator<< (HardwareSerial& serial, T data) 
{ 
    serial.print(data); 
    return serial; 
}

// Global variables
uint8_t tx_buffer[255];
bool warmup{false};
NTPtime NTPch{NTP_PROVIDER};
Si5351 si5351;
TinyGPSPlus gps;

// The serial connection to the GPS device
SoftwareSerial gpsSerial{GPS_RX_PIN, GPS_TX_PIN};

// Loop through the string, transmitting one character at a time.
void transmittWsprMessage()
{
    // Reset the tone to the base frequency and turn on the output
    Serial << "\n- TX ON - STARTING WSPR MESSAGE TRANSMISSION -";
    digitalWrite(TX_LED_PIN, LOW);
    
    si5351.output_enable(SI5351_CLK0, 1);
    
    for(uint8_t i{0}; i < WSPR_SYMBOL_COUNT; ++i)
    {
      si5351.set_freq((WSPR_DEFAULT_FREQ * 100) + (tx_buffer[i] * WSPR_TONE_SPACING), SI5351_CLK0);
      delay(WSPR_DELAY);
    }

    // Turn off the output
    si5351.output_enable(SI5351_CLK0, 0);

    Serial << "\n- TX OFF - END OF WSPR MESSAGE TRANSMISSION -";
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
    Serial << "\n- On-board LED initialization -";
    pinMode(TX_LED_PIN, OUTPUT);
    Serial << "\n- On-board LED successfully initialized! -";
}

static void wiFiInit()
{
    Serial << "\n- Establishing Wi-Fi connection to: " << SSID << " -";

    WiFi.mode(WIFI_OFF);
    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASSWORD);

    Serial << "\n- Connecting";

    const auto startTime{millis()};
    while (WiFi.status() != WL_CONNECTED && millis() <= startTime + INIT_MAX_TIME) {
        digitalWrite(TX_LED_PIN, LOW);
        delay(300);
        digitalWrite(TX_LED_PIN, HIGH);
        delay(300);
        Serial << ".";
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial << "\n- Connected to: " << SSID << " -";
        Serial << "\n- IP address: " << WiFi.localIP() << " -";
    }
    else
    {
        Serial << "\n- Not conected to: " << SSID << " -";
        Serial << "\n- Time synchronization via NTP will not be available! -";
    }
}

static void gpsInit()
{
    Serial << "\n- GPS initialization -";
    
    gpsSerial.begin(GPS_BAUDRATE);

    Serial << "\n- Getting data from GPS";
    
    const auto startTime{millis()};
    while (!gpsSerial.available() && millis() <= startTime + INIT_MAX_TIME)
    {
        delay(600);
        Serial << ".";
    }

    if (gpsSerial.available())
    {
        gps.encode(gpsSerial.read());
        Serial << "\n- GPS successfully initialized! -";
    }
    else
    {
        Serial << "\n- No GPS detected: check wiring! -";
    }
}

static void si5351Init()
{
    Serial << "\n- SI5351 initialization -";
    si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);
    si5351.set_correction(SI5351_CAL_FACTOR, SI5351_PLL_INPUT_XO);
    // Set CLK0 output
    si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_8MA); // Set for max power if desired
    si5351.output_enable(SI5351_CLK0, 0); // Disable the clock initially
    Serial << "\n- SI5351 successfully initialized! -";
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

static bool ntpDateTimeSync()
{
    uint8_t attempts{0};

    while (attempts <= MAX_SYNC_ATTEMPTS)
    {
        const auto& dateTime{NTPch.getNTPtime(TIME_ZONE, 1)};
        delay(SYNC_DELAY);
        ++attempts;

        if (dateTime.valid)
        {
            setTime(dateTime.hour, dateTime.minute, dateTime.second, dateTime.day, dateTime.month, dateTime.year);
            return true;
        }
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
    Serial << "\n- Date & time sychronization -";

    if (gpsDateTimeSync())
    {
        Serial << "\n- Date & time synchronized by GPS: "<< currentDateTime() <<" -";
    }
    else if (ntpDateTimeSync())
    {
        Serial << "\n- Date & time synchronized by NTP: "<< currentDateTime() << " -";
    }
    else
    {
        Serial << "\n- Time sync not available! -";
        Serial << "\n- Transmitting a WSPR message without time synchronization is impossible! -";
        Serial << "\n- Check your GPS and Wi-Fi connection settings and try again! -";
        exit(0);
    }

    return now();
}

void setup()
{
    // Serial port initialization
    Serial.begin(ESP_SERIAL_PORT_BAUDRATE); 
    while (!Serial);

    // Welcome message & working frequency info
    Serial << "\n**********************************************";
    Serial << "\n[ WSPR BEACON ]";
    Serial << "\n- Working frequency: " << WSPR_DEFAULT_FREQ / 1000000.0 << " MHz -";
    Serial << "\n**********************************************";

    // Use the NodeMCU on-board LED as a keying indicator
    ledInit();

    // WiFi initialization
    wiFiInit();

    // GPS module initialization
    gpsInit();

    // Set time sync provider
    NTPch.setSendInterval(SEND_INTV);
    NTPch.setRecvTimeout(RECV_TIMEOUT);
    setSyncProvider(dateTimeSyncronization);
  
    // Initialize the Si5351
    si5351Init();

    Serial << "\n**********************************************";
    Serial << "\n- Entering WSPR TX loop...";
    digitalWrite(TX_LED_PIN, HIGH);
    Serial << "\n**********************************************";

    // Encode the message in the transmit buffer
    // This is RAM intensive and should be done separately from other subroutines
    setWsprTxBuffer();
}

void loop()
{
    if((minute() + 1) % 4 == 0 && second() == 30 && !warmup)
    {
        warmup = true;
        Serial << "\n- Radio module warm up started! -";
        si5351.set_freq(WSPR_DEFAULT_FREQ * 100, SI5351_CLK0);
        si5351.output_enable(SI5351_CLK0, 1);
    }

    if(minute() % 4 == 0 && second() == 0)
    {
        warmup = false; 
        Serial << "\n- Start of transmission time: " << currentDateTime() << " -";
        Serial << "\n- WSPR message: " << WSPR_CALL << " " << WSPR_LOC << " " << WSPR_DBM << " -";
        transmittWsprMessage();
        setSyncProvider(dateTimeSyncronization);
        Serial << "\n**********************************************";
    }
}
