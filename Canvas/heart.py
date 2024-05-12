import time

import numpy as np
from PIL import Image

from Config.config import Config
from Misc.utils import rgb_to_hex, time_to_np


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
            (self.config.visuals.size.height, self.config.visuals.size.width, 7),
            dtype=np.uint8,
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

    def pixel_since(self, ts: int | float) -> list[tuple[int, int, str]] | None:
        """
        Returns all pixels that were modified since the given timestamp
        Args:
            ts: timestamp

        Returns:
            A dictionary with the modified pixels

        Output format: [
            [
                x (int),
                y (int),
                color (str)
            ]
        ]
        """
        if isinstance(ts, float):
            ts = int(ts)
        timestamps = (
            np.frombuffer(self.data[:, :, 3:].tobytes(), dtype=np.uint32)
            .astype(np.uint32)
            .byteswap(True)
        )
        colors = self.data[:, :, :3]

        filtered = np.where((timestamps >= ts) & (timestamps != 0))
        if len(filtered[0]) == 0:
            return []

        coords = np.array(np.unravel_index(filtered[0], self.data.shape[:2])).T

        pixels = np.empty((coords.shape[0], 3), dtype=object)
        pixels[:, :2] = coords

        pixels[:, 2] = np.vectorize(rgb_to_hex)(*colors[coords[:, 0], coords[:, 1]].T)

        pixels[:, [0, 1, 2]] = pixels[
            :, [1, 0, 2]
        ]  # transform from [y, x, color] to [x, y, color]

        out = pixels.tolist()
        # 1 Pixel = 5ms time * 200px = 1s reload time in browser
        if len(out) > 200:
            return None
        return out

    def create_image(self) -> Image:
        """
        Creates an image from the canvas array
        Returns:
            The created image
        """
        image = Image.fromarray(self.data[:, :, :3])
        return image
