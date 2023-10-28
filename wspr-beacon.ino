#include <ESP8266WiFi.h>
#include <int.h>
#include <JTEncode.h>
#include <NTPtimeESP.h>
#include <rs_common.h>
#include <si5351.h>
#include <string.h>
#include <TimeLib.h>
#include <WiFiClient.h>

#include "Wire.h"

// WSPR-specific defines
#define WSPR_TONE_SPACING       146
#define WSPR_DELAY              683

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

// Hardware defines
#define TX_LED_PIN                 2
#define SI5351_CAL_FACTOR          92000

// Class instantiation
Si5351 si5351;
JTEncode jtencode;

// Global variables
const char call[] = "NOCALL";
const char loc[] = "----";
const uint8_t dbm = 10;
uint8_t tx_buffer[255];

// NTP related global variables
NTPtime NTPch("time.windows.com");   
strDateTime dateTime;

// WiFi parameters
const char* ssid = "NAME";
const char* password = "PASSWORD";

// NTP parameters
#define SEND_INTV     10
#define RECV_TIMEOUT  10
#define TIME_ZONE     +1.0f

bool warmup = false;

// Loop through the string, transmitting one character at a time.
void encode()
{
  // Reset the tone to the base frequency and turn on the output
  Serial.println("- TX ON - STARTING WSPR TRANSMISSION...");
  digitalWrite(TX_LED_PIN, LOW);
  
  si5351.output_enable(SI5351_CLK0, 1);
  
  for(uint8_t i = 0; i < WSPR_SYMBOL_COUNT; i++)
  {
    si5351.set_freq((WSPR_DEFAULT_FREQ * 100) + (tx_buffer[i] * WSPR_TONE_SPACING), SI5351_CLK0);
    delay(WSPR_DELAY);
  }

  // Turn off the output
  si5351.output_enable(SI5351_CLK0, 0);

  Serial.println("- TX OFF - END OF WSPR TRANSMISSION...");
  digitalWrite(TX_LED_PIN, HIGH);
}

void set_tx_buffer()
{
  // Clear out the transmit buffer
  memset(tx_buffer, 0, 255);
  
  jtencode.wspr_encode(call, loc, dbm, tx_buffer);
}

void ssidConnect()
{
  Serial.print("- ESTABLISHING WIFI CONNECTION TO: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
 
  Serial.print("- Connecting");
 
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(TX_LED_PIN, LOW);
    delay(300);
    digitalWrite(TX_LED_PIN, HIGH);
    delay(300);
    Serial.print(".");
  }
     
  Serial.println();
  Serial.print(F("- Connected to: "));
  Serial.println(ssid);
  Serial.print(F("- IP address: "));
  Serial.println(WiFi.localIP());
}

time_t epochUnixNTP()
{
  digitalWrite(TX_LED_PIN, LOW);
  
  Serial.println("- NTP Time Sync...");

  NTPch.setSendInterval(SEND_INTV);
  NTPch.setRecvTimeout(RECV_TIMEOUT);
  do
  {
    dateTime = NTPch.getNTPtime(TIME_ZONE, 1);
    delay(1);
  }
  while(!dateTime.valid);
  Serial.print("- NTP Time: ");
  NTPch.printDateTime(dateTime);
  setTime(dateTime.hour,dateTime.minute,dateTime.second,dateTime.day,dateTime.month,dateTime.year); 
  
  digitalWrite(TX_LED_PIN, HIGH);
  
  return 0;
}

void setup()
{
  // Serial port initialization
  Serial.begin(115200); while (!Serial);
  Serial.println();
  Serial.println("[ WSPR BEACON ]");
  Serial.print("Working frequency: ");
  Serial.print(WSPR_DEFAULT_FREQ / 1000000.0, 4);
  Serial.println(" MHz");

  // WiFi initialization
  WiFi.mode(WIFI_OFF);
  WiFi.mode(WIFI_STA);
  ssidConnect();

  // Set time sync provider
  setSyncProvider(epochUnixNTP);

  // Initialize the Si5351
  Serial.println("- SI5351 initialization -");
  si5351.init(SI5351_CRYSTAL_LOAD_8PF, 0, 0);
  si5351.set_correction(SI5351_CAL_FACTOR, SI5351_PLL_INPUT_XO);
  // Set CLK0 output
  si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_8MA); // Set for max power if desired
  si5351.output_enable(SI5351_CLK0, 0); // Disable the clock initially
  Serial.println("- SI5351 successfully initialized! -");
  
  // Use the NodeMCU on-board LED as a keying indicator.
  Serial.println("- On-board LED initialization -");
  pinMode(TX_LED_PIN, OUTPUT);
  Serial.println("- On-board LED successfully initialized! -");

  Serial.println("- Entering WSPR TX loop...");
  digitalWrite(TX_LED_PIN, HIGH);

  // Encode the message in the transmit buffer
  // This is RAM intensive and should be done separately from other subroutines
  set_tx_buffer();
}

void loop()
{
  if((minute() + 1) % 4 == 0 && second() == 30 && !warmup)
  { 
    warmup = true;
    Serial.println("- Radio Module Warm up Started...");
    si5351.set_freq(WSPR_DEFAULT_FREQ * 100, SI5351_CLK0);
    si5351.output_enable(SI5351_CLK0, 1);
  }

  if(minute() % 4 == 0 && second() == 0)
  { 
    Serial.print("- Start of Transmission Time: ");
    time_t t = now();
    String formattedTime = String(year(t)) + "-" +
                          String(month(t)) + "-" +
                          String(day(t)) + " " +
                          String(hour(t)) + ":" +
                          String(minute(t)) + ":" +
                          String(second(t));

    Serial.println(formattedTime);
    encode();
    warmup = false;
    delay(4000);
    setSyncProvider(epochUnixNTP);
  }

}
