
import argparse
import subprocess
from pathlib import Path
import tempfile
import serial


BAUD_RATE = 115200
ser = serial.Serial(baudrate=BAUD_RATE, timeout=1)

def serial_attempt_connect(ser_port):
    ser.port = ser_port
    print("Attempting to connect to serial port " + ser_port)
    try:
        ser.open()
        print(ser_port + " is connected")
    except (serial.SerialException):
        raise IOError("Unable to connect. The device may be unplugged, another program may be using the COM port, or an incorrect COM port may have been given.")

def run(args):
  with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
    for line in process.stdout:
      print(line.decode('utf8'), end="")
  return process.returncode

def get_elf_start_addr(elf_path):
  start_addr = None
  readelf_str = "arm-none-eabi-readelf -l " + str(elf_path)
  with subprocess.Popen(readelf_str.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
    for line_num, line in enumerate(process.stdout):
      if(line_num == 7):
        tokens = line.decode('utf8').split()
        start_addr = tokens[3]
        return start_addr
  raise OSError("unable to parse elf file")

def create_binary(elf_path):
  temp_file = tempfile.NamedTemporaryFile(delete_on_close=False, delete=False)
  print("temp_file name =", str(temp_file.name))
  create_bin_str = "arm-none-eabi-objcopy --input-target elf32-littlearm --output-target binary " + str(elf_path) + " " + str(temp_file.name)
  run(create_bin_str.split())
  return Path(temp_file.name)

def erase_MCU(device_path):
  erase_str = "stm32flash -b "+ str(BAUD_RATE) + " -o " + device_path
  run(erase_str.split())

def flash_MCU(elf_path, reset_arg, device_path):
  start_address = get_elf_start_addr(elf_path)
  print(f"start address is {start_address}")
  bin_file = create_binary(elf_path)

  flash_str = "stm32flash -b " + str(BAUD_RATE) + " -w " + str(bin_file) + \
              " -v -f " + reset_arg + " -S " + start_address + " " + device_path
  run(flash_str.split())
  bin_file.unlink()

def parse_args():
  # Instantiate the parser
  parser = argparse.ArgumentParser()
  parser.add_argument("action", help = "either \"erase\" or the path to an ELF file")
  parser.add_argument("-d", help = "set the device path (default = /dev/ttyUSB0)", dest = "device_path", default = "/dev/ttyUSB0")
  parser.add_argument("-R", help = "reset device at exit", dest = "reset_device", action = 'store_true')

  args = parser.parse_args()
  return args

def main():

  args = parse_args()

  if(args.reset_device):
    reset_arg = "-R"
  else:
    reset_arg = ""

  print(f"device = {args.device_path}")

  try:
    serial_attempt_connect(args.device_path)
    ser.write(b"update\r\n")
  finally:
    ser.close()

  if (args.action == "erase"):
    erase_MCU(args.device_path)
  else:
    elf_path = Path(args.action).resolve(strict=True)
    flash_MCU(elf_path, reset_arg, args.device_path)


if __name__ == "__main__":
  main()
