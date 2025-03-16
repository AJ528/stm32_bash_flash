#!/bin/bash -x

POSITIONAL_ARGS=()

device="/dev/ttyUSB0"
baud="115200"
reset_option=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -d)
      device="$2"
      shift # past argument
      shift # past value
      ;;
    -R)
      reset_option="$1"
      shift
      ;;
    -*)
      echo "Unknown option" $1
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [[ -n $1 ]]; then


  if [ "$1" = "erase" ]; then
    stm32flash -b $baud -o $device
  else
    echo "device = $device"

    # read the ELF to determine where the binary file should be loaded
    start_addr=$(arm-none-eabi-readelf -l $1 | head -n 8 | tail -n 1 | xargs | cut -d " " -f 4) 
    echo "start address = $start_addr"

    # create a temporary file and store the binary output there
    temp_file=$(mktemp)
    arm-none-eabi-objcopy --input-target elf32-littlearm --output-target binary $1 $temp_file

    # load the binary file onto the microcontroller
    stm32flash -b $baud -w $temp_file -v $reset_option -S $start_addr $device

    # remove the temp file
    rm $temp_file
  fi
else
  echo "ERROR: must specify \"erase\" or provide path to elf file"
fi



