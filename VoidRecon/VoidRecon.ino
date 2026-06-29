// main.cpp
#include <Arduino.h>
#include <EEPROM.h>
#include <SPI.h>
#include "cli.h"

// Pin definitions
#define SCK_PIN 18
#define MISO_PIN 23
#define MOSI_PIN 19
#define SS_PIN 5
#define GDO0_PIN 2
#define GDO2_PIN 4

// Constants
#define BUF_LENGTH 128
#define EPROM_SIZE 512

// Global objects
CommandHandler cli;

void setup() {
    Serial.begin(115200);
    Serial.println();
    
    // Initialize EEPROM
    EEPROM.begin(EPROM_SIZE);
    
    // Setup SPI pins
    ELECHOUSE_cc1101.setSpiPin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
    ELECHOUSE_cc1101.setGDO(GDO0_PIN, GDO2_PIN);
    
    // Initialize command handler
    cli.init();
    Serial.println("Type 'help' for available commands");
    Serial.print("> ");
}

void loop() {
    static char buffer[BUF_LENGTH];
    static int length = 0;
    
    // Handle CLI input
    while (Serial.available()) {
        int data = Serial.read();
        
        if (data == '\b' || data == '\177') {  // Backspace/DEL
            if (length > 0) {
                length--;
                if (cli.isChatMode()) {
                    Serial.write('\b');
                }
            }
        }
        else if (data == '\r' || data == '\n') {
            if (!cli.isChatMode()) {
                Serial.write('\n');
            }
            buffer[length] = '\0';
            if (length > 0 && !cli.isChatMode()) {
                cli.processLine(buffer);
                Serial.print("vd1 > ");
            }
            length = 0;
        }
        else if (length < BUF_LENGTH - 1) {
            buffer[length++] = data;
            if (cli.isChatMode()) {
                // Chat mode handles its own echo
            }
        }
    }
    
    // Handle RF operations
    if (!cli.isChatMode()) {
        cli.handleRx();
        cli.handleJam();
    } else {
        cli.handleChat();
    }
}
