"""
Dreame 1C MIIO wrapper – FULL version
Compatibile con Home Assistant 2026+
Basato sul codice originale Romans3, migliorato e normalizzato.
"""

import logging
import socket
import struct
import time
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

MIIO_PORT = 54321
MIIO_TIMEOUT = 5


# ---------------------------------------------------------------------------
# DATA MODEL NORMALIZZATO
# ---------------------------------------------------------------------------

@dataclass
class DreameVacuumState:
    status: int
    error: int
    battery: int

    fan_speed: int
    water_level: int

    area: float
    timer: int

    total_clean_count: int
    total_area: float

    brush_life_level: int
    brush_left_time: int

    brush_life_level2: int
    brush_left_time2: int

    filter_life_level: int
    filter_left_time: int


# ---------------------------------------------------------------------------
# CLIENT MIIO RAW (NO PYTHON-MIIO)
# ---------------------------------------------------------------------------

class DreameVacuum:
    """
    Wrapper MIIO raw per Dreame 1C.
    Basato sul protocollo originale del progetto Romans3.
    """

    def __init__(self, host: str, token: str):
        self._host = host
        self._token = bytes.fromhex(token)
        self._device_id = None
        self._stamp = None

        _LOGGER.debug("DreameVacuum initialized for %s", host)

    # ----------------------------------------------------------------------
    # LOW LEVEL MIIO
    # ----------------------------------------------------------------------

    def _send(self, payload: bytes) -> bytes:
        """Invia un pacchetto MIIO raw e ritorna la risposta."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(MIIO_TIMEOUT)

        try:
            sock.sendto(payload, (self._host, MIIO_PORT))
            data, _ = sock.recvfrom(1024)
            return data
        except Exception as err:
            _LOGGER.error("MIIO communication error: %s", err)
            raise
        finally:
            sock.close()

    # ----------------------------------------------------------------------
    # HIGH LEVEL COMMANDS
    # ----------------------------------------------------------------------

    def status(self) -> DreameVacuumState:
        """Ottiene lo stato completo del Dreame 1C."""
        try:
            from .dreame_protocol import DreameProtocol
        except Exception:
            raise RuntimeError("Missing dreame_protocol.py")

        proto = DreameProtocol(self._host, self._token)
        raw = proto.get_status()

        return DreameVacuumState(
            status=raw["state"],
            error=raw["error"],
            battery=raw["battery"],

            fan_speed=raw["fan_speed"],
            water_level=raw["water_level"],

            area=raw["clean_area"],
            timer=raw["clean_time"],

            total_clean_count=raw["total_clean_count"],
            total_area=raw["total_clean_area"],

            brush_life_level=raw["main_brush_life"],
            brush_left_time=raw["main_brush_time"],

            brush_life_level2=raw["side_brush_life"],
            brush_left_time2=raw["side_brush_time"],

            filter_life_level=raw["filter_life"],
            filter_left_time=raw["filter_time"],
        )

    # ----------------------------------------------------------------------
    # COMMANDS
    # ----------------------------------------------------------------------

    def start(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).start_clean()

    def stop(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).stop_clean()

    def pause(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).pause_clean()

    def return_home(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).return_home()

    def find(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).find_me()

    def set_fan_speed(self, speed: int):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).set_fan_speed(speed)

    def set_water_level(self, level: int):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).set_water_level(level)

    # ----------------------------------------------------------------------
    # EXTRA COMMANDS
    # ----------------------------------------------------------------------

    def reset_main_brush(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).reset_main_brush()

    def reset_side_brush(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).reset_side_brush()

    def reset_filter(self):
        from .dreame_protocol import DreameProtocol
        return DreameProtocol(self._host, self._token).reset_filter()
