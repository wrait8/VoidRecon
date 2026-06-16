# VoidRecon
 <img width="2281" height="501" alt="VoidRecon" src="https://github.com/user-attachments/assets/67ae50fb-6ab7-40da-aec2-cf8b88e918f8" />
> Sub-GHz RF Reconnaissance Platform

VoidRecon is a CC1101-based RF analysis platform designed for signal reconnaissance, protocol analysis, packet capture, and spectrum monitoring.

Currently targeting ESP32 hardware, with planned support for ATmega32U4-based devices.

## Features

* RF Packet Sniffer
* RAW RF Data Capture
* Princeton Signal Capture & Replay
* Frequency Analyzer
* RSSI Monitoring
* Packet Recording & Playback
* RAW Waveform Recording & Playback
* Multi-Modulation Support
* RF Chat Mode
* Persistent Storage

## Supported Modulations

* 2-FSK
* GFSK
* ASK/OOK
* 4-FSK
* MSK

## Supported Frequency Ranges

* 300–348 MHz
* 387–464 MHz
* 779–928 MHz

## Hardware

### Current

* ESP32
* CC1101

### Planned

* ATmega32U4
* Custom RF Hardware

## Example Commands

```text
analyze
rx
getrssi
rec
play
rxraw
recraw
recsig
playsig
```

## Disclaimer

VoidRecon is intended for RF research, education, interoperability testing, and authorized security assessments only.

---

Observe. Capture. Analyze.
