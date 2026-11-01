"""Constants for the Fluval BLE Light integration."""

from __future__ import annotations

DOMAIN = "fluval_ble"

# Config entry keys
CONF_ADDRESS = "address"
CONF_NAME = "name"
CONF_CHANNELS = "channels"

DEFAULT_CHANNELS = 4

# GATT UUIDs (Fluval / Inledco "tuner168" CC2541 controller)
SERVICE_UUID = "00001000-0000-1000-8000-00805f9b34fb"
CHAR_WRITE = "00001001-0000-1000-8000-00805f9b34fb"  # commands written here
CHAR_NOTIFY = "00001002-0000-1000-8000-00805f9b34fb"  # status notifications
CHAR_READ_REG = "00001004-0000-1000-8000-00805f9b34fb"  # handshake reads
CHAR_WRITE_REG = "00001005-0000-1000-8000-00805f9b34fb"  # handshake register select

# Protocol constants
HEADER = 0x68
CMD_MODE = 0x02
CMD_LED = 0x03
CMD_CHANNELS = 0x04
CMD_STATUS = 0x05
CMD_CYCLE = 0x07  # program the "automatic" sunrise/day/sunset/night schedule
CMD_TIME = 0x0E

MODE_MANUAL = 0x00
MODE_AUTO = 0x01
MODE_PRO = 0x02

MODES = {
    MODE_MANUAL: "manual",
    MODE_AUTO: "automatic",
    MODE_PRO: "professional",
}
MODES_REVERSE = {v: k for k, v in MODES.items()}

# Channel hardware range is 0..1000
CHANNEL_MAX = 1000
