/*
* CC1101 Band Calibration Tool
* -----------------------------------------------------------
* With this tool, you determine the exact offset values (clb)
* for the FSCTRL0 register for a specific frequency band.
* * The lower and upper limit frequencies of the band are
* sent each time. You measure the actual frequency with an SDR
* and enter it here. The program calculates from this the
* perfect correction values for setClb().
*/

#include <SmartRC_CC1101.h>

// ============================================================
// PIN CONFIGURATION
// ============================================================
#define SCK_PIN   18
#define MISO_PIN  23
#define MOSI_PIN  19
#define SS_PIN    5
#define GDO0_PIN  2
#define GDO2_PIN  4

SmartRC_CC1101 rf;

// States for the menu navigation
enum State { SELECT_BAND, MEASURE_LOW, MEASURE_HIGH };
State currentState = SELECT_BAND;

int bandSelect = 0;
float freqLow = 0.0;
float freqHigh = 0.0;
int clbLow = 0;
int clbHigh = 0;

unsigned long txTimer = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial);
  // Configure CC1101 pins
  rf.setSpiPin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
  rf.setGDO0(GDO0_PIN);
  
  rf.Init();

  if (!rf.getCC1101()) {
    Serial.println("ERROR: CC1101 not found!");
    while (1);
  }

  // Send a clear continuous tone (ASK/OOK) for the measurement
  rf.setCCMode(1);
  rf.setModulation(2);
  rf.setPA(10); 

  showMenu();
}

void loop() {
  // Send a LONG test packet every 1000ms so that the signal becomes massively visible in the SDR
  if (currentState == MEASURE_LOW || currentState == MEASURE_HIGH) {
    if (millis() - txTimer < 1000) {
      byte txPacket[60]; 
      memset(txPacket, 0xAA, 60); // Fills the 60-byte array completely with 0xAA
      rf.SendData(txPacket, 60); // Sends the extra-long package
    }else if (millis() - txTimer > 2000){
      txTimer = millis();
    }
  }

  // Process user inputs
  if (Serial.available() > 0) {
    // 1. Safely read text up to the end of the line (or timeout)
    String userInput = Serial.readStringUntil('\n');
   
    // 2. Remove invisible spaces and control characters (\r, \n)
    userInput.trim(); 
    
    // 3. Ignore empty inputs (e.g., only Enter pressed)
    if (userInput.length() == 0) return; 

    // 4. Convert the clean text into a decimal number
    float measuredFreq = userInput.toFloat();
    
    if (measuredFreq == 0.0) {
      Serial.println("Invalid input. Please enter a valid number.");
      return; 
    }

    switch (currentState) {
      case SELECT_BAND:
        handleBandSelect((int)measuredFreq);
        break;
        
      case MEASURE_LOW:
        clbLow = calcFSCTRL0(freqLow, measuredFreq);
        Serial.print("-> Calculated Offset (Low): ");
        Serial.println(clbLow);
        Serial.println("-------------------------------------------");
        
        // Switch to the higher frequency
        rf.setMHZ(freqHigh);
        Serial.print("Measure now at the UPPER end at: ");
        Serial.print(freqHigh, 3);
        Serial.println(" MHz.");
        Serial.println("Enter the precisely measured frequency in the SDR:");
        currentState = MEASURE_HIGH;
        break;

      case MEASURE_HIGH:
        clbHigh = calcFSCTRL0(freqHigh, measuredFreq);
        Serial.print("-> Calculated Offset (High): ");
        Serial.println(clbHigh);
        Serial.println("-------------------------------------------");
        
        // Output result
        showResult();
        showMenu();
        currentState = SELECT_BAND;
        break;
    }
  }
}

// Calculates the necessary FSCTRL0 value based on the deviation
int calcFSCTRL0(float targetFreq, float actualFreq) {
  // Read current FSCTRL0 value (as signed int8_t!)
  int8_t currentOffset = (int8_t)rf.SpiReadReg(0x0C); // 0x0C is FSCTRL0
  
  // Frequency deviation in MHz
  float freqDelta = targetFreq - actualFreq;
  
  // The resolution of the FSCTRL0 register is F_OSC / 2^14
  // At 26 MHz: 26.0 / 16384 = 0.001586914 MHz (approx. 1.59 kHz) per tick
  float stepSize = 26.0 / 16384.0;
  
  // How many ticks do we need to shift the offset?
  int offsetTicks = round(freqDelta / stepSize);
  
  // Calculate new value and limit to 8-bit signed (-128 to +127)
  int newOffset = currentOffset + offsetTicks;
  if (newOffset > 127) newOffset = 127;
  if (newOffset < -128) newOffset = -128;
  
  // Return the offset as an unsigned byte for the register (2's complement is preserved)
  return (byte)newOffset;
}

void handleBandSelect(int band) {
  bandSelect = band;
  switch (band) {
    case 1: freqLow = 300.0; freqHigh = 348.0; break;
    case 2: freqLow = 378.0; freqHigh = 464.0; break;
    case 3: freqLow = 779.0; freqHigh = 899.0; break;
    case 4: freqLow = 900.0; freqHigh = 928.0; break;
    default:
      Serial.println("Invalid frequency band! Please enter 1, 2, 3, or 4.");
      return;
  }
  
  Serial.print("\nStart calibration for band");
  Serial.println(bandSelect);
  
  rf.setMHZ(freqLow);
  
  Serial.println("-------------------------------------------");
  Serial.print("Measure now at the LOWER end at: ");
  Serial.print(freqLow, 3);
  Serial.println(" MHz.");
  Serial.println("Set the SDR to the frequency and search for the signal.");
  Serial.println("Enter the precisely measured frequency in MHz (e.g., 378.015):");
  
  currentState = MEASURE_LOW;
}

void showMenu() {
  Serial.println("Select the frequency band to be calibrated:");
  Serial.println(" 1 : 315 MHz Band (300 - 348 MHz)");
  Serial.println(" 2 : 433 MHz Band (378 - 464 MHz)");
  Serial.println(" 3 : 868 MHz Band (779 - 899 MHz)");
  Serial.println(" 4 : 915 MHz Band (900 - 928 MHz)");
  Serial.println("-> Enter 1, 2, 3, or 4 and press Enter:");
}

void showResult() {
  Serial.println();
  Serial.println("CALIBRATION SUCCESSFUL!");
  Serial.println();
  Serial.println("Copy the following line into the setup() function");
  Serial.println("of your future projects (BEFORE rf.Init()):");
  Serial.println();
  
  Serial.print("  rf.setClb(");
  Serial.print(bandSelect);
  Serial.print(", ");
  Serial.print(clbLow);
  Serial.print(", ");
  Serial.print(clbHigh);
  Serial.println(");");
  Serial.println();
  Serial.println("With that, this module is perfectly adjusted for this band!");
  Serial.println();
  delay(3000);
}
