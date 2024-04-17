import logging
import numpy as np

from Misc.eventhandler import EventHandler

logger = logging.getLogger("pixelframe")
logging.basicConfig(level=logging.INFO)

event_handler = EventHandler()


class NoFrontendException(Exception):
    def __init__(self):
        super().__init__("You cant disable all frontends!")


def confirm():
    inp = input("Do you want to continue? (Y/N) ")
    if inp.lower() == "y":
        return True
    else:
        exit(1)


def time_to_np(ts: int | float) -> np.ndarray:
    if isinstance(ts, float):
        ts = int(ts)
    ts_bytes = ts.to_bytes(4, byteorder="big")
    return np.frombuffer(ts_bytes, dtype=np.uint8)


def np_to_time(ts: np.ndarray) -> int:
    ts_bytes = bytes(ts)
    return int.from_bytes(ts_bytes, byteorder="big")
