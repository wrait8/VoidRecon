# VoidRecon
 <img width="2281" height="501" alt="VoidRecon" src="https://github.com/user-attachments/assets/67ae50fb-6ab7-40da-aec2-cf8b88e918f8" />
VoidRecon is an open source Sub-GHz RF pentest and reconnaissance platform built on the CC1101 transceiver. It provides packet sniffing, raw waveform capture/replay, fixed-code remote analysis, spectrum scanning, jamming, brute-forcing, and RF chat capabilities on sub-1 GHz bands. VoidRecon is currently implemented for ESP32 (with CC1101) hardware; ATmega32U4 support is planned.

Features
Packet Sniffer: Receive and log RF packets.
Frequency Analyzer: Scan and identify active channels across sub-GHz bands.
RSSI Monitoring: Display signal strength and link quality (LQI) of received packets.
RAW RF Capture/Replay: Record raw RF samples (rxraw, recraw) and replay them (playraw).
Fixed-Code Remote Capture/Replay: Record fixed-code remote signals (recsig) and replay them (playsig).
Packet Recording/Playback: Buffer incoming packets (rec), list (show), and replay (play) them.
Multi-Modulation Support: 2-FSK, GFSK, ASK/OOK, 4-FSK, MSK modes.
Configurable Radio Parameters: Set frequency, channel, data rate, deviation, RX bandwidth, output power, sync word/mode, address filtering, packet format, CRC, Manchester encoding, FEC, preamble length, etc.
Jamming Mode: Continuous transmit jamming on the selected band (jam).
Brute-Force Mode: Time-based brute forcing for fixed-code signals (brute).
RF Chat Mode: Peer-to-peer RF text chat between devices (chat).
Commands
Command	Description
analyze	Scan frequency range for active signals.
getrssi	Display RSSI/LQI of last packet.
rx	Toggle packet sniffing (on/off).
rxraw	Sniff raw RF samples at given interval (µs).
rec	Toggle recording packets to buffer.
recraw	Toggle recording raw RF samples (µs).
recsig	Toggle recording fixed-code remote signal.
add	Add frame(s) to the recording buffer (hex values).
show	Show recorded packet buffer.
flush	Clear the recording buffer.
play	Replay packets from buffer (0 = all or N-th).
playsig	Replay recorded fixed-code signal.
playraw	Replay raw RF samples with interval.
jam	Toggle continuous RF jamming (on/off).
brute	Brute-force fixed-code signal timing.
chat	Toggle RF chat mode (on/off).
set*	Configure radio parameters (frequency, modulation, etc.).

Examples
text
Copy
# Set frequency to 433.92 MHz and modulation to OOK (2)
setmhz 433.92
setmodulation 2

# Scan for signals and sniff packets
analyze
rx

# Record and replay
rec
play 0

# Capture raw samples
rxraw 200     (sample interval = 200 µs)
recraw 200
playraw 200
Supported Hardware
Current: ESP32 (with CC1101 transceiver)
Planned: ATmega32U4 (with CC1101)
Supported Frequencies
Sub-GHz Ranges: 300–348 MHz, 387–464 MHz, 779–928 MHz
Modulations: 2-FSK, GFSK, ASK/OOK, 4-FSK, MSK
Installation
Compile and flash VoidRecon to your ESP32 using PlatformIO or the Arduino IDE. No special toolchain is required beyond a standard ESP32 development setup.

License
MIT License

Disclaimer
VoidRecon is intended for authorized testing and educational use only. Users must comply with all applicable laws and RF regulations.
