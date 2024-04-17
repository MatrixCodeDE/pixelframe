import time

from Config.config import Config
from Misc.utils import time_to_np
import numpy as np


class Heart:
    """
    The heart of the canvas, that stores all the pixels with timestamps
    Attributes:
        config (Config): The config
        data (np.ndarray): The data of all the pixels
        timestamp (np.ndarray): The current timestamp in 4 Bytes

    Structure of data:
    y [
        x[
            7 Bytes / 8-Bit Integers:
                Byte 0-2: Colors RGB
                Byte 3-6: 32-Bit Integer Timestamp
        ]
    ]
    y and x are swapped so rows come before columns, rendered left-right, then top-bottom respectively
    """
    config: Config
    data: np.ndarray
    timestamp: np.ndarray

    def __init__(self, config: Config):
        self.config = config

        self.data = np.zeros(
            (
                self.config.visuals.size.height,
                self.config.visuals.size.width,
                7
            ),
            dtype=np.uint8
        )

        self.timestamp = np.zeros(4, dtype=np.uint8)

    def update_pixel(self, x: int, y: int, value: tuple[int, int, int]) -> None:
        """
        Updates a pixel at the position x, y with the values RGB
        Args:
            x (int): Coordinate x
            y (int): Coordinate y
            value (tuple[int, int, int]): Values RGB
        """
        self.data[y, x, :3] = np.array(value, dtype=np.uint8)
        self.data[y, x, 3:] = self.timestamp

    def get_pixel_color(self, x: int, y: int) -> tuple:
        """
        Returns the color of the pixel x, y
        Args:
            x (int): Coordinate x
            y (int): Coordinate y

        Returns:
            Tuple with the values RGB
        """
        data = self.data[y, x, :3]
        return tuple(data.tolist())

    def update_timestamp(self) -> None:
        """
        Updates the own timestamp frequently
        Returns:
            None
        """
        self.timestamp = time_to_np(time.time())

    def pixel_since(self, ts: int | float) -> dict:
        """
        Returns all pixels that were modified since the given timestamp
        Args:
            ts: timestamp

        Returns:
            A dictionary with the modified pixels

        Output format: {
            y: {
                x: {
                    "r": int

                    "g": int

                    "b": int
                }
            }
        }
        """
        if isinstance(ts, float):
            ts = int(ts)
        timestamps = self.data[:, :, 3].view(np.uint32)
        colors = self.data[:, :, :3]

        filtered = np.where((timestamps < ts) & (timestamps != 0))

        rgb_vals = colors[filtered]

        pixels = {}

        for y, x in zip(*filtered):
            if y not in pixels:
                pixels[y] = {}
            if x not in pixels[y]:
                pixels[y][x] = {}

            pixels[y][x]["r"] = rgb_vals[y, x, 0]
            pixels[y][x]["g"] = rgb_vals[y, x, 1]
            pixels[y][x]["b"] = rgb_vals[y, x, 2]

        return pixels

    def all_pixels(self) -> dict:
        """
        Returns all pixels of the canvas
        Returns:
            A dictionary with the pixels

        Output format: {
            y: {
                x: {
                    "r": int

                    "g": int

                    "b": int
                }
            }
        }
        """
        colors = self.data[:, :, :3]

        pixels = {}

        for y in range(self.config.visuals.size.height):
            for x in range(self.config.visuals.size.width):
                if y not in pixels:
                    pixels[y] = {}
                if x not in pixels[y]:
                    pixels[y][x] = {}

                pixels[y][x]["r"] = colors[y, x, 0]
                pixels[y][x]["g"] = colors[y, x, 1]
                pixels[y][x]["b"] = colors[y, x, 2]

        return pixels
