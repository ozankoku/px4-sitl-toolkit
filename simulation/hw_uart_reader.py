#!/usr/bin/env python
"""hw_uart_reader.py — Binary frame decoder for the ESP32 neighbour-beacon UART stream.

Reads 33-byte frames from the ESP32 over UART/serial.
Each frame begins with the SB magic bytes (0x53 0x42).

Firmware frame layout (33 bytes, indices 0–32):
  [0]     MAGIC_0  0x53 'S'
  [1]     MAGIC_1  0x42 'B'
  [2]     VERSION  0x02
  [3]     ID       uint8 (0–255)
  [4–7]  LAT      int32 LE  (× 10^7 deg)
  [8–11]  LON      int32 LE  (× 10^7 deg)
  [12–15] ALT      int32 LE  (mm)
  [16–19] VN       int32 LE  (mm/s)
  [20–23] VE       int32 LE  (mm/s)
  [24–27] VD       int32 LE  (mm/s)
  [28]    FLAGS    uint8
  [29]    RSVD     0x00
  [30]    RSVD     0x00
  [31]    RSVD     0x00
  [32]    CRC8     CRC-8 (poly 0x07, init 0) over bytes 0–31

Provides:
  _crc8(data)          — standalone CRC-8 helper
  ESP32UARTReader      — threaded serial reader with get_neighbours()
"""

import struct
import threading
import time

import numpy as np
import serial


SB_MAGIC   = b'\x53\x42'  # 'SB' — frame start magic
FRAME_SIZE = 33           # 33-byte frame: magic(2)+ver(1)+id(1)+fields(24)+flags(1)+rsvd(3)+crc(1)


def _crc8(data: bytes) -> int:
    """Compute CRC-8 checksum using polynomial 0x07 and initial value 0.

    Args:
        data: byte string to checksum.

    Returns:
        Single-byte CRC value as an integer in [0, 255].
    """
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


class ESP32UARTReader:
    """Threaded reader for the ESP32 neighbour-beacon binary protocol.

    Spawns a daemon thread that continuously reads from the serial port,
    decodes frames, validates CRC-8, and maintains a dict of recently
    seen neighbours keyed by drone ID.

    Args:
        port: Serial device path (e.g. '/dev/ttyAMA0' on Raspberry Pi).
        baud: Baud rate (default 115200).
    """

    def __init__(self, port: str = '/dev/ttyAMA0', baud: int = 115200):
        """Initialise reader with port and baud; does not open the serial port."""
        self._port = port
        self._baud = baud
        self._lock = threading.Lock()
        self._neighbours: dict = {}
        self._running = False
        self._thread = None

    def start(self):
        """Open the serial port and start the background reader thread."""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the reader thread to stop and wait for it to finish."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _read_loop(self):
        """Main loop: open serial, sync on SB magic, read frame, decode, repeat."""
        try:
            with serial.Serial(self._port, self._baud, timeout=1.0) as ser:
                buf = b''
                while self._running:
                    buf += ser.read(1)
                    if len(buf) < 2:
                        continue
                    # Scan for SB magic at buf[0:2]
                    if buf[0:2] != SB_MAGIC:
                        buf = buf[1:]  # slide window by one byte
                        continue
                    # Magic found — read the rest of the frame
                    remaining = FRAME_SIZE - 2
                    rest = ser.read(remaining)
                    if len(rest) != remaining:
                        buf = b''
                        continue
                    self._decode(buf[:2] + rest)
                    buf = b''
        except serial.SerialException as exc:
            print(f"ESP32UARTReader: serial error — {exc}")

    def _decode(self, frame: bytes):
        """Parse a 33-byte frame, validate CRC-8, and update the neighbours dict.

        Frame layout: see module docstring.  CRC-8 is over bytes 0–31;
        byte 32 is the transmitted CRC.

        Args:
            frame: 33-byte raw frame starting with SB magic.
        """
        if len(frame) != FRAME_SIZE:
            return
        if frame[0:2] != SB_MAGIC:
            return

        data_bytes   = frame[0:32]  # bytes 0–31: everything before CRC
        received_crc = frame[32]    # byte 32: transmitted CRC

        computed_crc = _crc8(data_bytes)
        if computed_crc != received_crc:
            return  # Discard corrupted frame

        p = frame  # alias for concise offset references
        uav_id  = frame[3]                        # uint8 ID at offset 3
        lat_enc = struct.unpack_from('<i', p, 4)[0]
        lon_enc = struct.unpack_from('<i', p, 8)[0]
        alt_enc = struct.unpack_from('<i', p, 12)[0]
        vn_enc  = struct.unpack_from('<i', p, 16)[0]
        ve_enc  = struct.unpack_from('<i', p, 20)[0]
        vd_enc  = struct.unpack_from('<i', p, 24)[0]
        status  = frame[28]                       # uint8 FLAGS

        # Convert to SI units
        lat_deg = lat_enc / 1e7
        lon_deg = lon_enc / 1e7
        alt_m   = alt_enc / 1000.0
        vn_m_s  = vn_enc  / 1000.0
        ve_m_s  = ve_enc  / 1000.0
        vd_m_s  = vd_enc  / 1000.0

        neighbour = {
            'id':        str(uav_id),
            'position':  np.array([lat_deg, lon_deg, alt_m]),
            'velocity':  np.array([vn_m_s, ve_m_s, vd_m_s]),
            'status':    status,
            'timestamp': time.monotonic(),
        }

        with self._lock:
            self._neighbours[str(uav_id)] = neighbour

    def get_neighbours(self) -> list:
        """Return a snapshot of currently tracked neighbours.

        Returns:
            List of neighbour dicts; safe to iterate without holding the lock.
        """
        with self._lock:
            return list(self._neighbours.values())


if __name__ == '__main__':
    import sys

    PORT = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyAMA0'
    print(f"ESP32UARTReader standalone test — listening on {PORT}")
    reader = ESP32UARTReader(port=PORT)
    reader.start()
    try:
        while True:
            neighbours = reader.get_neighbours()
            print(f"Neighbours ({len(neighbours)}): {neighbours}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        reader.stop()
