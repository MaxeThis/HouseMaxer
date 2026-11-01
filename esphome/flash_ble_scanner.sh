#!/bin/bash
# Flash the BLE scanner firmware onto an ESP32 plugged into this computer by USB.
# Same firmware for every board: each one names itself ble-scanner-<last 6 of MAC>.
#
# First time:  python3 -m venv ~/.venvs/esphome && ~/.venvs/esphome/bin/pip install esphome
#              cp secrets.example.yaml secrets.yaml   (then fill it in)
set -e
cd "$(dirname "$0")"
ESPHOME=${ESPHOME:-~/.venvs/esphome/bin/esphome}
PORT=$(ls /dev/cu.usbserial* /dev/cu.SLAB_USBtoUART* /dev/cu.wchusbserial* /dev/cu.usbmodem* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -1)
if [ -z "$PORT" ]; then
  echo "No ESP32 found on USB. Try another cable: many USB-C cables are charge-only."
  exit 1
fi
echo "Flashing $PORT (if it stalls at 'Connecting...', hold the BOOT button on the board)"
"$ESPHOME" run ble-scanner.yaml --device "$PORT" --no-logs
echo "Done. Unplug it, plug it into a USB wall charger where you want it,"
echo "then add it in Home Assistant: Settings -> Devices & services -> ESPHome."
