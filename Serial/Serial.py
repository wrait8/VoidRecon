import threading
import serial
import colorama
from colorama import Fore, Back, Style
import time
import sys
import os
import datetime
import readline
import atexit
import uuid
import argparse
import shutil
import subprocess

TIMEOUT_DURATION = 15 # seconds

# colorama.init(autoreset=True)
CYAN = Style.BRIGHT + Fore.CYAN
GREEN = Style.BRIGHT + Fore.GREEN
BLUE = Style.BRIGHT + Fore.BLUE
RED = Style.BRIGHT + Fore.RED
YELLOW = Style.BRIGHT + Fore.YELLOW
MAGENTA = Style.BRIGHT + Fore.MAGENTA
RESET = Fore.RESET

# === CONFIGURATION ===
PORT = "COM3"
BAUD = 115200

# === LOGGING SETUP ===
LOG_FILE = None
SESSION_ID = None
should_exit = False
is_reconnecting = False
exit_pressed = False

# === COMMAND LINE ARGUMENTS ===
parser = argparse.ArgumentParser(description='Serial Terminal with Logging')
parser.add_argument('--output', '-o', type=str, nargs='?', const='auto', help='Save log output')
parser.add_argument('--port', '-p', type=str, help=f'Serial port (default: {PORT})')
parser.add_argument('--baud', '-b', type=int, help=f'Baud rate (default: {BAUD})')
args = parser.parse_args()

if args.port:
    PORT = args.port
if args.baud:
    BAUD = args.baud

output_filename = None
if args.output:
    if args.output == 'auto':
        output_filename = None
    else:
        output_filename = args.output

# === COMMAND HISTORY SETUP ===
histfile = os.path.join(os.path.expanduser("~"), ".serial_terminal_history")
try:
    readline.read_history_file(histfile)
except FileNotFoundError:
    pass
atexit.register(readline.write_history_file, histfile)

# === SYSTEM COMMAND CHECK FUNCTION ===
def is_command_executable(command):
    """Check if a command exists on the system"""
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return False
    
    executable = cmd_parts[0]
    
    # Check if it's in PATH
    if shutil.which(executable):
        return True
    
    # Check for Windows extensions
    if sys.platform == 'win32':
        for ext in ['.exe', '.bat', '.cmd', '.ps1']:
            if shutil.which(executable + ext):
                return True
    
    return False

def execute_system_command(command):
    """Execute a system command and display output"""
    try:
        print(YELLOW + f"\n[*] Executing: {command}" + RESET)
        print("-" * 50)
        
        # Set timeout for command execution
        timeout = 30
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            # Print stdout
            if result.stdout:
                print(result.stdout, end='')
            
            # Print stderr
            if result.stderr:
                print(RED + result.stderr + RESET, end='')
            
            # Print return code if non-zero
            if result.returncode != 0 and result.returncode != 1:
                print(YELLOW + f"[!] Command exited with code: {result.returncode}" + RESET)
            
        except subprocess.TimeoutExpired:
            print(RED + f"[!] Command timed out after {timeout} seconds" + RESET)
        
        print("-" * 50)
        return True
        
    except Exception as e:
        print(RED + f"[!] Failed to execute: {e}" + RESET)
        print("-" * 50)
        return False

def save_log(data_buffer, log_file_path):
    """Save log to plain text file"""
    if data_buffer and log_file_path:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(''.join(data_buffer))
        print(GREEN + f"[+] Log saved to: {log_file_path}" + RESET)

def get_timestamp():
    return datetime.datetime.now().strftime("[%H:%M:%S]")

def ascii():
    ASCII = """
____   ____    .__    ._____________                            
\\   \ /   /___ |__| __| _/\\______   \ ____   ____  ____   ____  
 \\   Y   /  _ \\|  |/ __ |  |       _// __ \_/ ___\/  _ \ /    \\ 
  \\     (  <_> )  / /_/ |  |    |   \\  ___/\  \__(  <_> )   |  \\
   \\___/ \\____/|__\\____ |  |____|_  /\\___  >\\___  >____/|___|  /
                       \\/         \\/     \\/     \\/           \\/ """
    print(ASCII)

def initial_boot_message_logic():
    global should_exit
    try:
        print(YELLOW + "\r[?] " + RESET + "Consuming first boot messages . . .", end='', flush=True)
        initial_data = ""
        start_time = time.time()
        timeout = 1
        while time.time() - start_time < timeout and not should_exit:
            try:
                if ser and ser.is_open and ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting).decode(errors='ignore')
                    initial_data += data
                    start_time = time.time()
            except:
                pass
            time.sleep(0.01)
        print('\r' + ' ' * 50 + '\r', end='', flush=True)
    except:
        print('\r' + ' ' * 50 + '\r', end='', flush=True)

def serial_reconnection():
    global ser, is_reconnecting, should_exit, exit_pressed
    
    if is_reconnecting or should_exit:
        return
    
    is_reconnecting = True
    
    try:
        if ser and ser.is_open:
            ser.close()
    except:
        pass

    start_time = time.time()
    while time.time() - start_time < TIMEOUT_DURATION and not should_exit and not exit_pressed:
        try:
            print(YELLOW + "\r[?] " + RESET + f"Reconnection timeout {int(TIMEOUT_DURATION - (time.time() - start_time))} [PRESS ENTER TO EXIT] . . .", end='', flush=True)
            
            ser = serial.Serial(PORT, BAUD, timeout=0.1)
            print("\r" + " " * 80 + "\r", end="", flush=True) 
            print(BLUE + "\r[*] " + RESET + f"Reconnected [{PORT}, {BAUD}]", flush=True)
            time.sleep(0.5)
            initial_boot_message_logic()
            is_reconnecting = False
            return True
        
        except serial.SerialException:
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    
    if not should_exit:
        print("\r" + " " * 80 + "\r", end="", flush=True)
        print(RED + "\r[!] " + RESET + f"Failed to reconnect after {TIMEOUT_DURATION}s")
        should_exit = True
    
    is_reconnecting = False
    exit_pressed = True
    return False

def read_from_serial(log_buffer):
    global should_exit, is_reconnecting
    initial_boot_message_logic()
    
    while not should_exit:
        try:
            if ser and ser.is_open and ser.in_waiting > 0:
                data = ser.read(ser.in_waiting).decode(errors='ignore')
                if data:
                    print(data, end='', flush=True)
                    
                    if log_buffer is not None:
                        log_buffer.append(data)
            time.sleep(0.01)
        except (serial.SerialException, AttributeError, OSError, PermissionError):
            if not should_exit and not is_reconnecting:
                print(MAGENTA + "\n[^] " + RESET + "Serial connection lost.")
                serial_reconnection()
            time.sleep(0.5)
        except:
            break

def write_to_serial():
    global should_exit, exit_pressed, log_buffer
    while not should_exit and not exit_pressed:
        try:
            if sys.platform == 'win32':
                import msvcrt
                if msvcrt.kbhit():
                    line = sys.stdin.readline()
                else:
                    time.sleep(0.1)
                    continue
            else:
                line = sys.stdin.readline()
            
            if not line:
                break
            
            if line == "\n":
                if is_reconnecting:
                    exit_pressed = True
                    should_exit = True
                    break
                
            
            # Terminal commands
            if line.strip() == "clear":
                os.system("clear||cls")
                continue
            elif line.strip() == "banner":
                ascii()
                continue
            elif line.strip() == "quit":
                should_exit = True
                exit_pressed = True
                break
            elif line.strip() == "session":
                print(f"{MAGENTA}[^]{RESET} Session ID: {BLUE}{SESSION_ID}{RESET}")
                continue
            elif line.strip() == "help":
                    # Send to serial device
                    if ser and ser.is_open:
                        ser.write(line.encode())
                        
                        if log_buffer is not None:
                            timestamp = get_timestamp()
                            log_entry = f"{timestamp} >>> {line.strip()}"
                            log_buffer.append(log_entry)
            else:
                cmd = line.strip()
                
                # Check if the command exists on the system
                if is_command_executable(cmd):
                    # Execute system command
                    execute_system_command(cmd)
                    
                    # Log the command with timestamp
                    if log_buffer is not None:
                        timestamp = get_timestamp()
                        log_entry = f"{timestamp} >>> [SYSTEM] {cmd}"
                        log_buffer.append(log_entry)
                else:
                    # Send to serial device
                    if ser and ser.is_open:
                        ser.write(line.encode())
                        if log_buffer is not None:
                            timestamp = get_timestamp()
                            log_entry = f"{timestamp} >>> {line.strip()}"
                            log_buffer.append(log_entry)
        except KeyboardInterrupt:
            should_exit = True
            exit_pressed = True
            break
        except (serial.serialutil.PortNotOpenError, ValueError, AttributeError):
            if not should_exit:
                print(YELLOW + "\n[!] Not connected. Type 'quit' to exit." + RESET)
            continue
        except Exception as e:
            if not should_exit:
                print(YELLOW + f"\n[!] Error: {e}" + RESET)
            continue

def save_log_automatically(log_buffer):
    if not log_buffer:
        return
    
    global output_filename
    if output_filename:
        log_file_path = output_filename
    else:
        log_file_path = f"serial_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{SESSION_ID}.txt"
    
    save_log(log_buffer, log_file_path)

# === START BANNER ===
os.system("clear||cls")
ascii()

SESSION_ID = f"{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}"
print(f"{MAGENTA}[^]{RESET} Session ID: {BLUE}{SESSION_ID}{RESET}")
print()

print(YELLOW + "\r[?] " + RESET + f"Connecting to [{PORT}, {BAUD}] . . .", end='', flush=True)
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("\r" + " " * 50 + "\r", end="", flush=True)
except serial.SerialException:
    print("\r" + " " * 80 + "\r", end="", flush=True)
    print(RED + "[!] " + RESET + f"Port {PORT} hasn't been found.")
    exit()

log_buffer = []
t1 = threading.Thread(target=read_from_serial, args=(log_buffer,), daemon=True)
t2 = threading.Thread(target=write_to_serial, daemon=False)

t1.start()
t2.start()

try:
    t2.join()
except KeyboardInterrupt:
    should_exit = True
    exit_pressed = True
    pass

try:
    if ser and ser.is_open:
        ser.close()
except:
    pass

time.sleep(0.5)

if args.output:
    save_log_automatically(log_buffer)
