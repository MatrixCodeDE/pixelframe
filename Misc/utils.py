import logging
from typing import Any

import numpy as np

logger = logging.getLogger("pixelframe")
logging.basicConfig(level=logging.INFO)


class Status:
    """
    The status of every module
    Attributes:
        config (Config): The configuration
        api (bool): If the API is enabled
        display (bool): If the display is enabled
        socketserver (bool): If the socketserver (netcat) is enabled
    """
    config: None
    api: bool
    display: bool
    socketserver: bool

    def __init__(self):
        self.config = None
        self.api = False
        self.display = False
        self.socketserver = False

    def update(self, attribute: str, value: Any) -> bool:
        """
        Updates the status of the services of pixelframe
        """
        if hasattr(self, attribute):
            if type(getattr(self, attribute)) == type(value):
                setattr(self, attribute, value)
                return True
            elif attribute == "config":
                setattr(self, attribute, value)
        return False

    def get_status(self) -> dict:
        return {
            "api": {
                "state": "online" if self.api else "offline",
                "port": (
                    self.config.connection.ports.api
                    if self.config.frontend.api.enabled
                    else "-"
                ),
            },
            "display": {
                "state": "online" if self.display else "offline",
                "port": "Not supported",
            },
            "socketserver": {
                "state": "online" if self.socketserver else "offline",
                "port": (
                    self.config.connection.ports.socket
                    if self.config.frontend.sockets.enabled
                    else "-"
                ),
            },
        }


status = Status()


class NoFrontendException(Exception):
    """Exception if no frontend is enabled"""
    def __init__(self):
        super().__init__("You cant disable all frontends!")


def confirm():
    """CMD input confimation (Y/N)"""
    inp = input("Do you want to continue? (Y/N) ")
    if inp.lower() == "y":
        return True
    else:
        exit(1)


def time_to_np(ts: int | float) -> np.ndarray:
    """Converts a timestamp to a numpy array for the canvas"""
    if isinstance(ts, float):
        ts = int(ts)
    ts_bytes = ts.to_bytes(4, byteorder="big")
    return np.frombuffer(ts_bytes, dtype=np.uint8)


def np_to_time(ts: np.ndarray) -> int:
    """Converts a canvas numpy array entry to a timestamp"""
    ts_bytes = bytes(ts)
    return int.from_bytes(ts_bytes, byteorder="big")


def rgb_to_hex(
    r: int | np.uint8,
    g: int | np.uint8,
    b: int | np.uint8,
    a: int | np.uint8 | None = None,
) -> str:
    """Transforms  RGB(A) to a hexadecimal string"""
    if a:
        return "%02x%02x%02x%02x" % (r, g, b, a)
    else:
        return "%02x%02x%02x" % (r, g, b)


def hex_to_rgb(hexa: str) -> tuple[int, int, int] | tuple[int, int, int, int] | None:
    """Transforms a hexadecimal string to RGB(A)"""
    c = int(hexa, 16)
    if len(hexa) == 6:
        r = (c & 0xFF0000) >> 16
        g = (c & 0x00FF00) >> 8
        b = c & 0x0000FF
        return r, g, b
    elif len(hexa) == 8:
        r = (c & 0xFF000000) >> 24
        g = (c & 0x00FF0000) >> 16
        b = (c & 0x0000FF00) >> 8
        a = c & 0x000000FF
        return r, g, b, a
    else:
        return None


def cooldown_to_text(cooldown: float) -> str:
    """Transforms the cooldown to a string (seconds/milliseconds)"""
    if cooldown < 1:
        return f"{cooldown*1000:.2f} milliseconds"
    else:
        return f"{cooldown:.2f} seconds"
