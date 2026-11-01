"""Protocol + BLE transport for Fluval Bluetooth LED controllers.

The controller is a tuner168 CC2541 module used across the FluvalSmart range
(Aquasky 2.0, Plant 3.0, Flex, Marine/Nano, etc.). Commands are XOR-obfuscated
frames written to a GATT characteristic; status comes back as multi-packet
notifications. The wire format was reverse engineered by the Home Assistant
community (mrzottel's ESPHome `fluval_ble_led` component) and is reimplemented
here in pure Python on top of Bleak so it can run on Home Assistant's own
Bluetooth stack (the Raspberry Pi adapter or an ESPHome Bluetooth proxy).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime
import logging

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import (
    CHAR_NOTIFY,
    CHAR_READ_REG,
    CHAR_WRITE,
    CHAR_WRITE_REG,
    CMD_CHANNELS,
    CMD_CYCLE,
    CMD_LED,
    CMD_MODE,
    CMD_STATUS,
    CMD_TIME,
    HEADER,
    MODE_AUTO,
    MODE_MANUAL,
)

_LOGGER = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Framing: CRC + XOR "encryption"
# --------------------------------------------------------------------------- #
def _add_crc(data: list[int]) -> list[int]:
    """Append an XOR checksum byte over the plaintext frame."""
    crc = 0
    for b in data:
        crc ^= b
    return [*data, crc]


def encrypt(plaintext: list[int]) -> bytes:
    """Wrap a plaintext frame (CRC already appended) into a wire packet.

    Each byte is XORed with 0x0E, then a 3-byte header is prepended:
    [0x54, (len+1) ^ 0x54, 0x5A].
    """
    body = [b ^ 0x0E for b in plaintext]
    secret = (len(body) + 1) ^ 0x54
    return bytes([0x54, secret, 0x5A, *body])


def decrypt(packet: bytes) -> bytes:
    """Decrypt a notification packet. Key = byte0 ^ byte2; payload XOR key."""
    if len(packet) < 4:
        return b""
    key = packet[0] ^ packet[2]
    return bytes(b ^ key for b in packet[3:])


def build_frame(payload: list[int]) -> bytes:
    """CRC + encrypt a plaintext payload, ready to write."""
    return encrypt(_add_crc(payload))


# --------------------------------------------------------------------------- #
# Status model
# --------------------------------------------------------------------------- #
class FluvalStatus:
    """Last known state of the light."""

    def __init__(self) -> None:
        self.available = False
        self.on = False
        self.mode = MODE_MANUAL
        self.channels: list[int] = [0, 0, 0, 0, 0]
        # Current "automatic" schedule read back from the device, or None.
        # {sunrise_start, sunrise_end, sunset_start, sunset_end: minutes-of-day,
        #  day: [..], night: [..] channel bytes}
        self.auto: dict | None = None
        # Full plaintext bytes of the last decoded auto status frame, so we can
        # read-modify-write while preserving turn-off / dynamic (cloud) fields.
        self.auto_raw: list[int] | None = None

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"FluvalStatus(available={self.available}, on={self.on}, "
            f"mode={self.mode}, channels={self.channels}, auto={self.auto})"
        )


# --------------------------------------------------------------------------- #
# Device
# --------------------------------------------------------------------------- #
class FluvalDevice:
    """Manages a persistent BLE connection to one Fluval light."""

    def __init__(
        self,
        ble_device_provider: Callable[[], BLEDevice | None],
        num_channels: int = 4,
        address: str | None = None,
    ) -> None:
        """Initialize.

        ble_device_provider returns a fresh BLEDevice each connect attempt so
        Home Assistant can hand us whichever adapter/proxy currently sees it.
        """
        self._provider = ble_device_provider
        self.num_channels = num_channels
        self.address = address
        self.status = FluvalStatus()

        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._buffer = bytearray()
        self._listeners: list[Callable[[], None]] = []
        self._closing = False
        self._reconnect_task: asyncio.Task | None = None

    @property
    def mac(self) -> str:
        """Best-known MAC address for this light."""
        if self.address:
            return self.address
        dev = self._provider()
        return dev.address if dev else ""

    # -- listener plumbing -------------------------------------------------- #
    def add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        """Register a state-change callback. Returns an unsubscribe function."""
        self._listeners.append(cb)

        def _remove() -> None:
            if cb in self._listeners:
                self._listeners.remove(cb)

        return _remove

    def _notify_listeners(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:  # noqa: BLE001 - never let a callback kill us
                _LOGGER.exception("Fluval listener callback failed")

    # -- connection lifecycle ---------------------------------------------- #
    async def connect(self) -> None:
        """Establish the connection and run the handshake."""
        async with self._lock:
            if self._client is not None and self._client.is_connected:
                return
            device = self._provider()
            if device is None:
                raise ConnectionError("Fluval light not currently in range")

            _LOGGER.debug("Connecting to Fluval light %s", device.address)
            client = await establish_connection(
                BleakClient,
                device,
                device.address,
                disconnected_callback=self._on_disconnect,
            )
            self._client = client

            await client.start_notify(CHAR_NOTIFY, self._on_notify)
            await self._handshake()
            self.status.available = True
            self._notify_listeners()
            _LOGGER.info("Connected to Fluval light %s", device.address)

    async def _handshake(self) -> None:
        """Replay the app's init sequence, then request current status.

        The "password" read from CHAR_READ_REG is only validated inside the
        official app, so we read and discard it. Time is synced because the
        controller has no RTC and needs it for auto/pro schedules.
        """
        client = self._client
        assert client is not None
        # Register select 0x0F, read (password) and discard
        await client.write_gatt_char(CHAR_WRITE_REG, bytes([0x0F]), response=True)
        try:
            await client.read_gatt_char(CHAR_READ_REG)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Handshake read 1 failed (continuing): %s", err)
        # Register select 0x47, read (sw version) and discard
        await client.write_gatt_char(CHAR_WRITE_REG, bytes([0x47]), response=False)
        try:
            await client.read_gatt_char(CHAR_READ_REG)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Handshake read 2 failed (continuing): %s", err)
        await self._sync_time()
        await self._send([HEADER, CMD_STATUS])

    async def _sync_time(self) -> None:
        """Send the current local time to the controller."""
        now = datetime.now()
        # Controller day-of-week: 1=Mon..7=Sun -> store as Python isoweekday.
        frame = [
            HEADER,
            CMD_TIME,
            now.year - 2000,
            now.month,
            now.day,
            now.isoweekday(),
            now.hour,
            now.minute,
            now.second,
        ]
        await self._send(frame)

    def _on_disconnect(self, _client: BleakClient) -> None:
        _LOGGER.warning("Fluval light disconnected")
        self.status.available = False
        self._buffer.clear()
        self._notify_listeners()
        if not self._closing:
            self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.ensure_future(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        delay = 5
        while not self._closing and not self.status.available:
            await asyncio.sleep(delay)
            if self._closing:
                return
            try:
                await self.connect()
                return
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Fluval reconnect failed: %s", err)
                delay = min(delay * 2, 60)

    async def disconnect(self) -> None:
        """Tear down the connection (e.g. on unload)."""
        self._closing = True
        if self._reconnect_task:
            self._reconnect_task.cancel()
        async with self._lock:
            if self._client is not None:
                try:
                    await self._client.disconnect()
                finally:
                    self._client = None

    # -- notifications ------------------------------------------------------ #
    def _on_notify(self, _char: BleakGATTCharacteristic, data: bytearray) -> None:
        """Reassemble multi-packet status notifications and decode."""
        decrypted = decrypt(bytes(data))
        if not decrypted:
            return
        # A 17-byte decrypted chunk means "more to follow"; anything shorter is
        # the final chunk of the frame.
        if decrypted and decrypted[0] == HEADER and len(decrypted) == 17:
            # Start of a fresh multi-packet frame
            self._buffer = bytearray(decrypted)
            return
        if len(decrypted) == 17 and self._buffer:
            self._buffer.extend(decrypted)
            return
        # Final chunk
        self._buffer.extend(decrypted)
        frame = bytes(self._buffer)
        self._buffer.clear()
        self._decode_status(frame)

    def _decode_status(self, frame: bytes) -> None:
        if len(frame) < 5 or frame[0] != HEADER or frame[1] != CMD_STATUS:
            return
        # CRC over the whole frame must be zero
        crc = 0
        for b in frame:
            crc ^= b
        if crc != 0:
            _LOGGER.debug("Discarding Fluval status with bad CRC")
            return
        self.status.mode = frame[2]
        chns = self._num_channels_for_decode()
        if self.status.mode == MODE_MANUAL:
            # [0x68,0x05,mode,on,dyn, ch1lo,ch1hi, ...]
            self.status.on = (frame[3] & 0x01) != 0x00
            chans = []
            for i in range(5):
                lo_idx = 5 + i * 2
                hi_idx = 6 + i * 2
                if hi_idx < len(frame):
                    chans.append((frame[hi_idx] << 8) | (frame[lo_idx] & 0xFF))
                else:
                    chans.append(0)
            self.status.channels = chans
        elif self.status.mode == MODE_AUTO:
            # [0x68,0x05,mode, srSH,srSM,srEH,srEM, day[chns], ssSH,ssSM,ssEH,ssEM, night[chns], ...]
            self.status.on = True
            self.status.channels = [0, 0, 0, 0, 0]
            need = 11 + 2 * chns
            if len(frame) >= need + 1:
                day = list(frame[7 : 7 + chns])
                night = list(frame[11 + chns : 11 + 2 * chns])
                self.status.auto = {
                    "sunrise_start": frame[3] * 60 + frame[4],
                    "sunrise_end": frame[5] * 60 + frame[6],
                    "day": day,
                    "sunset_start": frame[7 + chns] * 60 + frame[8 + chns],
                    "sunset_end": frame[9 + chns] * 60 + frame[10 + chns],
                    "night": night,
                }
                self.status.auto_raw = list(frame)
                _LOGGER.debug(
                    "Fluval AUTO schedule read: %s | raw=%s",
                    self.status.auto,
                    frame.hex(),
                )
        else:
            # professional mode: schedule points not parsed here
            self.status.on = True
            self.status.channels = [0, 0, 0, 0, 0]
        self._notify_listeners()

    def _num_channels_for_decode(self) -> int:
        return self.num_channels if self.num_channels in (4, 5) else 4

    # -- low level write ---------------------------------------------------- #
    async def _send(self, payload: list[int]) -> None:
        """CRC, fragment, encrypt and write a plaintext command.

        The CC2541 controller only supports the minimum 23-byte ATT MTU, so a
        write payload may be at most ~20 bytes. Long commands (e.g. the auto
        schedule) are split into <=17-byte payload fragments, each encrypted
        independently with its own 3-byte header — the same framing the device
        uses for its multi-packet status notifications. A 17-byte fragment means
        "more to follow"; the final fragment is shorter.
        """
        client = self._client
        if client is None or not client.is_connected:
            raise ConnectionError("Not connected to Fluval light")
        full = _add_crc(list(payload))
        fragments = [full[i : i + 17] for i in range(0, len(full), 17)]
        multi = len(fragments) > 1
        # Single-fragment commands use an acked Write Request (reliable). Long
        # commands are sent as Write-Without-Response fragments with a short gap
        # between them, mirroring the official app's transport.
        for n, fragment in enumerate(fragments):
            try:
                await client.write_gatt_char(
                    CHAR_WRITE, encrypt(fragment), response=not multi
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "Fluval write fragment %d/%d failed: %s", n + 1, len(fragments), err
                )
                raise
            if multi:
                await asyncio.sleep(0.02)
        if multi:
            _LOGGER.debug(
                "Fluval sent %d-byte command in %d fragments", len(full), len(fragments)
            )

    async def _write(self, packet: bytes) -> None:
        client = self._client
        if client is None or not client.is_connected:
            raise ConnectionError("Not connected to Fluval light")
        await client.write_gatt_char(CHAR_WRITE, packet, response=True)

    async def _ensure_connected(self) -> None:
        if self._client is None or not self._client.is_connected:
            await self.connect()

    # -- public commands ---------------------------------------------------- #
    async def async_request_status(self) -> None:
        """Ask the controller to push its current status."""
        await self._ensure_connected()
        await self._send([HEADER, CMD_STATUS])

    async def async_set_power(self, on: bool) -> None:
        """Turn the light on or off."""
        await self._ensure_connected()
        await self._send([HEADER, CMD_LED, 0x01 if on else 0x00])
        self.status.on = on
        self._notify_listeners()

    async def async_set_mode(self, mode: int) -> None:
        """Switch between manual (0), automatic (1), professional (2)."""
        await self._ensure_connected()
        await self._send([HEADER, CMD_MODE, mode])
        self.status.mode = mode
        self._notify_listeners()
        # Pull fresh channel state after a mode change
        await self._send([HEADER, CMD_STATUS])

    async def async_set_channels(self, channels: list[int]) -> None:
        """Set channel levels (each 0..1000). Requires manual mode."""
        await self._ensure_connected()
        vals = [max(0, min(1000, int(c))) for c in channels]
        # Ensure we have enough channels; pad with current state.
        while len(vals) < self.num_channels:
            vals.append(0)
        payload = [HEADER, CMD_CHANNELS]
        for i in range(self.num_channels):
            v = vals[i]
            payload.append((v >> 8) & 0xFF)
            payload.append(v & 0xFF)
        await self._send(payload)
        self.status.channels = (vals + [0, 0, 0, 0, 0])[:5]
        self._notify_listeners()
        await self._send([HEADER, CMD_STATUS])

    async def async_set_auto_schedule(
        self,
        sunrise_start: int,
        sunrise_end: int,
        day: list[int],
        sunset_start: int,
        sunset_end: int,
        night: list[int],
        turnoff: int | None = None,
    ) -> None:
        """Program the on-device "automatic" schedule (CMD_CYCLE, 0x07).

        Times are minutes-of-day (0..1439). day/night are per-channel byte
        levels (0..255). turnoff is an optional minutes-of-day to switch off,
        or None to disable. Frame layout (plaintext, before CRC/encrypt):
        [0x68, 0x07, srSH, srSM, srEH, srEM, day[n],
         ssSH, ssSM, ssEH, ssEM, night[n], (toEN, toH, toM)?]
        """
        await self._ensure_connected()
        n = self.num_channels

        def _clamp_levels(vals: list[int]) -> list[int]:
            out = [max(0, min(255, int(v))) for v in vals]
            while len(out) < n:
                out.append(0)
            return out[:n]

        def _hm(minutes: int) -> tuple[int, int]:
            m = max(0, min(1439, int(minutes)))
            return m // 60, m % 60

        srsh, srsm = _hm(sunrise_start)
        sreh, srem = _hm(sunrise_end)
        sssh, sssm = _hm(sunset_start)
        sseh, ssem = _hm(sunset_end)
        day_lv = _clamp_levels(day)
        night_lv = _clamp_levels(night)

        raw = self.status.auto_raw
        if raw is not None and len(raw) >= 11 + 2 * n + 1:
            # Read-modify-write: keep the controller's existing frame structure
            # (turn-off + dynamic/cloud fields and exact length) and overwrite
            # only the sunrise/day/sunset/night fields. raw = [0x68,0x05,mode,
            # <fields...>, CRC]; the CMD_CYCLE write uses the same field layout.
            fields = list(raw[3:-1])
            fields[0:4] = [srsh, srsm, sreh, srem]
            fields[4 : 4 + n] = day_lv
            fields[4 + n : 8 + n] = [sssh, sssm, sseh, ssem]
            fields[8 + n : 8 + 2 * n] = night_lv
            if turnoff is not None and len(fields) >= 8 + 2 * n + 3:
                th, tm = _hm(turnoff)
                fields[8 + 2 * n : 8 + 2 * n + 3] = [0x01, th, tm]
            payload = [HEADER, CMD_CYCLE, *fields]
        else:
            payload = [HEADER, CMD_CYCLE, srsh, srsm, sreh, srem]
            payload += day_lv
            payload += [sssh, sssm, sseh, ssem]
            payload += night_lv
            if turnoff is not None:
                th, tm = _hm(turnoff)
                payload += [0x01, th, tm]

        _LOGGER.debug("Fluval applying AUTO schedule payload: %s", bytes(payload).hex())
        await self._send(payload)
        # Give the controller a moment to store it, then re-read (twice, spaced).
        await asyncio.sleep(0.5)
        await self._send([HEADER, CMD_STATUS])
        await asyncio.sleep(1.0)
        await self._send([HEADER, CMD_STATUS])
