/*
 * A simple sketch that uses WiServer to get the hourly weather data from LAX and prints
 * it via the Serial API
 */
 
 // this sketch uses a keepalive flag
 // to test remote server, should i use this?
 // http://hruska.us/tempmon/BBQ_Controller.pde
 
 // also look at
 // https://github.com/asynclabs/WiShield/blob/master/WiServer.h

#include <WiServer.h>
#include <SoftwareSerial.h>

#define WIRELESS_MODE_INFRA	1
#define WIRELESS_MODE_ADHOC	2

# define to 1 to get serial output
#define DEBUG 0

// Wireless configuration parameters ----------------------------------------
 //skiff
unsigned char local_ip[] = {192,168,1,92};	// IP address of WiShield
unsigned char gateway_ip[] = {192,168,1,1};	// router or gateway IP address
unsigned char subnet_mask[] = {255,255,255,0};	// subnet mask for the local network
const prog_char ssid[] PROGMEM = {"theskiff"};		// max 32 bytes

unsigned char security_type = 3;	// 0 - open; 1 - WEP; 2 - WPA; 3 - WPA2

// WPA/WPA2 passphrase
const prog_char security_passphrase[] PROGMEM = {"iamamate"};	// max 64 characters

/*
 //home
unsigned char local_ip[] = {192,168,1,115};	// IP address of WiShield
unsigned char gateway_ip[] = {192,168,1,254};	// router or gateway IP address
unsigned char subnet_mask[] = {255,255,255,0};	// subnet mask for the local network
const prog_char ssid[] PROGMEM = {"ethomenet"};		// max 32 bytes

unsigned char security_type = 3;	// 0 - open; 1 - WEP; 2 - WPA; 3 - WPA2

// WPA/WPA2 passphrase
const prog_char security_passphrase[] PROGMEM = {"E1C49BC515"};	// max 64 characters
*/

// WEP 128-bit keys
// sample HEX keys
prog_uchar wep_keys[] PROGMEM = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d,	// Key 0
				  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,	// Key 1
				  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,	// Key 2
				  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00	// Key 3
				};

// setup the wireless mode
// infrastructure - connect to AP
// adhoc - connect to another WiFi device
unsigned char wireless_mode = WIRELESS_MODE_INFRA;

unsigned char ssid_len;
unsigned char security_passphrase_len;
// End of wireless configuration parameters ----------------------------------------

short int nbr_dashes = 0; // nbr dashes we've seen
boolean msg_found = 0; // True if we're look at message content from our server

// pin constants
const int buttonPin = 6;     // the number of the pushbutton pin
const int rxPin = 7;
const int txPin = 8;
SoftwareSerial printer = SoftwareSerial(rxPin, txPin);

const byte command = 0x1B;

const byte fullcut = 0x69;
const byte partialcut = 0x6D;

void cut() {
  printer.print(command, BYTE);
  printer.print(fullcut, BYTE);
}

// Function that prints data from the server
void printData(char* data, int len) {
  //Serial.print("Got something to print:");
  //Serial.println(len);
  // Print the data returned by the server
  // Note that the data is not null-terminated, may be broken up into smaller packets, and 
  // includes the HTTP header. 
  while (len-- > 0) {
    char cur_char = *data;
    if (msg_found) {
      if (DEBUG) {
        Serial.print(cur_char); // debug output to console
      }
      printer.print(cur_char); // output for printer
    }
    // we need to see -------------- to start/end msgs
    if (cur_char == '-') {
      nbr_dashes += 1;
      //Serial.print("Dashes:");
      //Serial.println(nbr_dashes);
      if (nbr_dashes == 14) {
        //Serial.println("BINGO!");
        //Serial.println(msg_found);
        if (msg_found == 1) {
          // we were printing a msg, now we're finishing
          // so we print a carriage return
          printer.println();
          printer.println();
          printer.println();
          printer.println();
          cut();
        }
        msg_found = !msg_found;
      }
    } else {
      nbr_dashes = 0;
    }
    data++;
    //Serial.print(*(data++));
  } 
}


// IP Address for www.weather.gov  
//uint8 ip[] = {140,90,113,200};
uint8 ip[] = {74,53,73,66}; //aicookbook/ianozsvald vps ip

// A request that gets the latest METAR weather data for LAX
//GETrequest getWeather(ip, 80, "www.weather.gov", "/data/METAR/KLAX.1.txt");
GETrequest getWeather(ip, 80, "microprinter.ianozsvald.com", "/");


// Time (in millis) when the data should be retrieved 
long updateTime = 0;//millis();//0;

void setup() {
   // initialize the pushbutton pin as an input:
  pinMode(buttonPin, INPUT);   
 
  pinMode(rxPin, INPUT);
  pinMode(txPin, INPUT); // dummy config

  if (DEBUG) {
    Serial.begin(19200);   
    Serial.print("About to initialise WiServer...\n");
  }
    // Initialize WiServer (we'll pass NULL for the page serving function since we don't need to serve web pages) 
  WiServer.init(NULL);


  pinMode(txPin, OUTPUT);
  printer.begin(19200);
  printer.print("Microprinter is warming up...\n");


  printer.print("\n\nWiServer initialised...\n\n\n\n");
  if (DEBUG) {
    Serial.print("WiServer initialised...\n");
  }
  // Enable Serial output and ask WiServer to generate log messages (optional)
  
  WiServer.enableVerboseMode(true);
  //Serial.print("test3\n");
  // Have the processData function called when data is returned by the server
  getWeather.setReturnFunc(printData);
  
  updateTime = millis(); // set this to the current time
  
  //Serial.begin(19200); //open the USB connection too for input
  
}

//void println(char text[]) {
//  printer.println(text);
//}



void loop(){

  // read the state of the pushbutton value:
  int buttonState = digitalRead(buttonPin);
  
  // Check if it's time to get an update
  if ((millis() >= updateTime) && (getWeather.isActive() == false)) {
    //Serial.println("!!time for update");
    if (buttonState == HIGH) {
      // Get another update later
      updateTime += 1000 * 5; // *10 would be 10 secs// * 60 * 60;
      
      msg_found = 0; // force reset to 'no message found yet'

      if (DEBUG) {
        Serial.println("!!time for update and button is pressed\n");
      }
      //Serial.println(millis());
      getWeather.submit();   
      //println("hello from ian\n\n\n"); 
      //printer.println('X');

      //Serial.print(millis());
      //Serial.print(",");
      //Serial.println(updateTime);
    }
  }
  if (DEBUG) {
    if (getWeather.isActive()){
      Serial.print(".");
    }// else {
  //  Serial.print("isActive==False\n");
 // }
  }
  
  
  // Run WiServer
  WiServer.server_task();
  delay(10); // 10 ms
}
