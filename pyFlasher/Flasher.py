#!/usr/bin/env python3
"""
VoidRecon Firmware(v0.1.0-beta.1) Flasher
"""

import os
import sys
import time
import subprocess
import argparse
import serial
import serial.tools.list_ports
from colorama import init, Fore, Back, Style
import threading
import re

# Initialize colorama
init(autoreset=True)

# Color definitions
CYAN = Style.BRIGHT + Fore.CYAN
GREEN = Style.BRIGHT + Fore.GREEN
BLUE = Style.BRIGHT + Fore.BLUE
RED = Style.BRIGHT + Fore.RED
YELLOW = Style.BRIGHT + Fore.YELLOW
MAGENTA = Style.BRIGHT + Fore.MAGENTA
WHITE = Style.BRIGHT + Fore.WHITE
RESET = Fore.RESET
DIM = Style.DIM

VERSION = "1.0.0"
APP_NAME = "VoidRecon Firmware Uploader"

# === ASCII BANNER ===
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MAGENTA + r"""
        _                        
       `*-.                    
        )  _`-.                 
       .  : `. .                
       : _   '  \               
       ; *` _.   `*-._  [@wrait8]  
       `-.-'          `-.       
         ;       `       `.     
         :.       .        \    
         . \  .   :   .-'   .   
         '  `+.;  ;  '      :   
         :  '  |    ;       ;-. 
         ; '   : :`-:     _.`* ;
      .*' /  .*' ; .*`- +'  `*' 
      `*-*   `*-*  `*-*'        
    """ + RESET)

 
    print(BLUE + "[*] OS: " + sys.platform + " | " + time.strftime("%Y-%m-%d %H:%M:%S") + RESET)
    print()

# === PORT DETECTION ===
def get_ports():
    """Get list of available serial ports"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def auto_detect_Device():
    """Try to auto-detect ESP32 device"""
    print("[APP]"+ " Scanning for Device devices...", end=" ", flush=True)
    ports = get_ports()
    
    # Common ESP32/Device VID/PIDs or keywords
    keywords = ['USB', 'COM', 'ttyUSB', 'ttyACM', 'cu.usbmodem', 'cu.usbserial']
    
    for port in ports:
        # Check if port name contains typical USB keywords
        if any(keyword in port.lower() for keyword in ['usb', 'com', 'tty']):
            print(GREEN + "[FOUND]" + RESET)
            print(DIM + "    └─ " + port + RESET)
            return port
    
    print(RED + "[NOT FOUND]" + RESET)
    return None

# === FIRMWARE OPERATIONS ===
def check_esptool():
    """Check if esptool is available via python -m"""
    # Check if esptool module is available
    try:
        result = subprocess.run([sys.executable, '-m', 'esptool', '--version'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return True, 'python -m esptool'
    except:
        pass
    
    # Fallback: check for esptool.py in PATH
    try:
        result = subprocess.run(['esptool.py', '--version'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return True, 'esptool.py'
    except:
        pass
    
    # Fallback: check for esptool.exe in PATH
    try:
        result = subprocess.run(['esptool.exe', '--version'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return True, 'esptool.exe'
    except:
        pass
    
    return False, None

def install_esptool():
    """Install esptool via pip"""
    print(YELLOW + "[!] " + RESET + "esptool not found. Installing...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'esptool'], check=True)
        print(GREEN + "[+] " + RESET + "esptool installed successfully!")
        return True
    except:
        print(RED + "[!] " + RESET + "Failed to install esptool")
        print(DIM + "    └─ Please install manually:" + RESET)
        print(DIM + "        pip install esptool" + RESET)
        return False

def get_esptool_cmd():
    """Get the available esptool command"""
    has_esptool, cmd = check_esptool()
    if has_esptool:
        return cmd
    return None

def ensure_esptool():
    """Ensure esptool is available, install if not"""
    has_esptool, cmd = check_esptool()
    if has_esptool:
        return True, cmd
    
    print(YELLOW + "[!] " + RESET + "esptool not found. Installing automatically...")
    if install_esptool():
        # Check again after install
        has_esptool, cmd = check_esptool()
        if has_esptool:
            return True, cmd
    
    return False, None

def build_esptool_cmd(port, baud, *args):
    """Build the esptool command with the preferred method"""
    has_esptool, cmd_type = check_esptool()
    
    if cmd_type == 'python -m esptool':
        # Use python -m esptool
        cmd = [sys.executable, '-m', 'esptool', '--port', port, '--baud', str(baud)] + list(args)
    elif cmd_type == 'esptool.py':
        cmd = ['esptool.py', '--port', port, '--baud', str(baud)] + list(args)
    elif cmd_type == 'esptool.exe':
        cmd = ['esptool.exe', '--port', port, '--baud', str(baud)] + list(args)
    else:
        # Fallback to python -m esptool
        cmd = [sys.executable, '-m', 'esptool', '--port', port, '--baud', str(baud)] + list(args)
    
    return cmd

def erase_flash(port, baud=460800):
    """Erase ESP32 flash"""
    print(YELLOW + "[?] " + RESET + "Erasing flash...", end=" ", flush=True)
    try:
        cmd = build_esptool_cmd(port, baud, 'erase_flash')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(GREEN + "[DONE]" + RESET)
            return True
        else:
            print(RED + "[FAILED]" + RESET)
            print(DIM + "    └─ " + result.stderr.strip() + RESET)
            return False
    except Exception as e:
        print(RED + "[FAILED]" + RESET)
        print(DIM + "    └─ " + str(e) + RESET)
        return False

def upload_firmware(port, firmware_path, baud=460800, address="0x1000"):
    """Upload firmware to ESP32"""
    if not os.path.exists(firmware_path):
        print(RED + "[!] " + RESET + f"Firmware file not found: {firmware_path}")
        return False
    
    # Check file extension
    if not firmware_path.endswith('.bin'):
        print(YELLOW + "[!] " + RESET + "Warning: File doesn't have .bin extension")
    
    # Get file size
    file_size = os.path.getsize(firmware_path)
    size_kb = file_size / 1024
    
    print(MAGENTA + "[^] " + RESET + f"Uploading firmware ({size_kb:.2f} KB)...", end=" ", flush=True)
    print(DIM + f"\n    └─ Address: {address}" + RESET)
    print(DIM + f"    └─ Baud: {baud}" + RESET)
    
    try:
        cmd = build_esptool_cmd(port, baud, 'write_flash', address, firmware_path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(GREEN + "\n[+] " + RESET + "Firmware uploaded successfully!")
            return True
        else:
            print(RED + "\n[!] " + RESET + "Upload failed!")
            print(DIM + "    └─ " + result.stderr.strip() + RESET)
            return False
    except subprocess.TimeoutExpired:
        print(RED + "\n[!] " + RESET + "Upload timed out!")
        return False
    except Exception as e:
        print(RED + "\n[!] " + RESET + f"Error: {e}")
        return False

def verify_firmware(port, firmware_path, address="0x1000"):
    """Verify uploaded firmware"""
    print(YELLOW + "[?] " + RESET + "Verifying firmware...", end=" ", flush=True)
    try:
        cmd = build_esptool_cmd(port, 460800, 'verify_flash', address, firmware_path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(GREEN + "[OK]" + RESET)
            return True
        else:
            print(RED + "[FAILED]" + RESET)
            return False
    except:
        print(YELLOW + "[SKIPPED]" + RESET)
        return False

# === INTERACTIVE UI ===
def interactive_upload():
    """Interactive firmware upload session"""
    banner()
    print("[APP] " + RESET + "Waiting for you to connect your Device")
    
    # Auto-detect or manual port selection
    port = auto_detect_Device()
    
    if not port:
        print(YELLOW + "[!] " + RESET + "No device detected automatically.")
        print(DIM + "    └─ Available ports:" + RESET)
        ports = get_ports()
        if ports:
            for i, p in enumerate(ports):
                print(DIM + f"        {i+1}. {p}" + RESET)
            print()
            choice = input(YELLOW + "[?] " + RESET + "Select port (number) or enter manually: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(ports):
                    port = ports[idx]
                else:
                    port = choice
            except:
                port = choice
        else:
            port = input(YELLOW + "[?] " + RESET + "Enter port manually (e.g., COM4 or /dev/ttyUSB0): ").strip()
    
    if not port:
        print(RED + "[!] " + RESET + "No port selected. Exiting.")
        return
    
    print("[APP] " + RESET + f"Device connected on port {port}")
 
    # Check for esptool
    if not check_esptool():
        print(YELLOW + "[!] " + RESET + "esptool not found!")
        install = input(YELLOW + "[?] " + RESET + "Install esptool? (y/n): ").strip().lower()
        if install == 'y':
            if not install_esptool():
                return
        else:
            print(RED + "[!] " + RESET + "esptool is required to upload firmware.")
            return
    
    firmware_path = input(YELLOW + "[INPUT] " + "Enter the path of your Device firmware" + RESET +  DIM + "(e.g., 'path/file.bin') > ")
    
    if not firmware_path:
        print(RED + "[!] " + RESET + "No firmware path provided.")
        return
    
    # Expand user path if needed
    if firmware_path.startswith('~'):
        firmware_path = os.path.expanduser(firmware_path)
    
    # Make relative path absolute
    if not os.path.isabs(firmware_path):
        firmware_path = os.path.abspath(firmware_path)
    
    print(CYAN + "[APP] " + RESET + f"Looking for '{os.path.basename(firmware_path)}'")
    
    if not os.path.exists(firmware_path):
        print(RED + "[!] " + RESET + f"Firmware file not found: {firmware_path}")
        return
    
    # Ask for address
    address = input(YELLOW + "[?] " + RESET + "Flash address [default: 0x1000]: ").strip()
    if not address:
        address = "0x1000"
    
    # Ask for baud rate
    baud = input(YELLOW + "[?] " + RESET + "Baud rate [default: 460800]: ").strip()
    if not baud:
        baud = 460800
    else:
        try:
            baud = int(baud)
        except:
            print(YELLOW + "[!] " + RESET + "Invalid baud rate, using default 460800")
            baud = 460800
    
    # Confirmation
    print()
    print(DIM + "    └─ Port: " + port + RESET)
    print(DIM + "    └─ Firmware: " + firmware_path + RESET)
    print(DIM + "    └─ Address: " + address + RESET)
    print(DIM + "    └─ Baud: " + str(baud) + RESET)
    print()
    
    confirm = input(YELLOW + "[?] " + RESET + "Proceed with upload? (y/n): ").strip().lower()
    if confirm != 'y':
        print(RED + "[!] " + RESET + "Upload cancelled.")
        return
    
    # Erase flash
    print()
    print(CYAN + "[OPR] " + RESET + "Erasing Device flash...")
    if not erase_flash(port, baud):
        retry = input(YELLOW + "[?] " + RESET + "Retry erase? (y/n): ").strip().lower()
        if retry == 'y':
            if not erase_flash(port, baud):
                print(RED + "[!] " + RESET + "Erase failed. Aborting.")
                return
        else:
            print(YELLOW + "[!] " + RESET + "Skipping erase...")
    
    # Upload firmware
    print()
    print(CYAN + "[OPR] " + RESET + "Uploading firmware to Device...")
    if upload_firmware(port, firmware_path, baud, address):
        # Verify
        print()
        verify = input(YELLOW + "[?] " + RESET + "Verify firmware? (y/n): ").strip().lower()
        if verify == 'y':
            verify_firmware(port, firmware_path, address)
    else:
        print(RED + "[!] " + RESET + "Firmware upload failed!")
    
    print()
    print("[APP] " + RESET + "Done!")
    print(DIM + "    └─ " + time.strftime("%Y-%m-%d %H:%M:%S") + RESET)

# === COMMAND LINE MODE ===
def main():
    parser = argparse.ArgumentParser(
        description='VoidRecon Firmware Uploader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python uploader.py                     # Interactive mode
  python uploader.py -p COM4 -f firmware.bin  # Direct upload
  python uploader.py -p COM4 -f firmware.bin -a 0x1000 -b 460800
        '''
    )
    
    parser.add_argument('-p', '--port', help='Serial port (e.g., COM4, /dev/ttyUSB0)')
    parser.add_argument('-f', '--firmware', help='Path to firmware .bin file')
    parser.add_argument('-a', '--address', default='0x1000', help='Flash address (default: 0x1000)')
    parser.add_argument('-b', '--baud', type=int, default=460800, help='Baud rate (default: 460800)')
    parser.add_argument('--no-erase', action='store_true', help='Skip flash erase')
    parser.add_argument('--verify', action='store_true', help='Verify after upload')
    
    args = parser.parse_args()
    
    # If no arguments, run interactive
    if not args.port and not args.firmware:
        interactive_upload()
        return
    
    # Command line mode
    if not args.port or not args.firmware:
        print(RED + "[!] " + RESET + "Both --port and --firmware are required in command line mode")
        parser.print_help()
        return
    
    banner()
 
    # Check esptool
    if not check_esptool():
        print(RED + "[!] " + RESET + "esptool not found!")
        sys.exit(1)
    
    print("[APP] " + RESET + f"Device connected on port {args.port}")
    print("[APP] " + RESET + f"Firmware: {args.firmware}")
    
    # Erase flash
    if not args.no_erase:
        print(BLUE + "[OPR] " + RESET + "Erasing Device flash...")
        if not erase_flash(args.port, args.baud):
            print(YELLOW + "[!] " + RESET + "Erase failed. Continuing anyway...")
    
    # Upload
    print()
    print(BLUE + "[OPR] " + RESET + "Uploading firmware to Device...")
    if upload_firmware(args.port, args.firmware, args.baud, args.address):
        if args.verify:
            verify_firmware(args.port, args.firmware, args.address)
    else:
        print(RED + "[!] " + RESET + "Firmware upload failed!")
        sys.exit(1)
    
    print()
    print(GREEN + "[APP] " + RESET + "Done!")
    print(DIM + "    └─ " + time.strftime("%Y-%m-%d %H:%M:%S") + RESET)

if __name__ == "__main__":
    main()
