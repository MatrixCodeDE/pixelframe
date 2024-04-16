import time
from collections import deque
from typing import Any, Callable, Optional

from gevent import spawn
from gevent.time import sleep as gsleep
from greenlet import GreenletExit
from PIL import Image

from Config.config import Config
from Misc.Template.pixelmodule import PixelModule
from Misc.utils import event_handler
from Stats.stats import Stats


class Pixel(object):
    """An object for storing pixel with easy and clear structure"""

    x: int
    y: int
    r: int
    g: int
    b: int
    a: int

    def __init__(self, x: int, y: int, r: int, g: int, b: int, a: int = 255):
        self.x = x
        self.y = y
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def get(self):
        """Returns the Pixel formatted for Pillow"""
        return (self.x, self.y), (self.r, self.g, self.b, self.a)


class Queue:
    """The queue for pixels to set at the canvas"""

    queue: deque

    def __init__(self) -> None:
        """
        Initializes the queue with a deque
        """
        self.queue = deque()

    def add(self, pixel: Pixel) -> None:
        """
        Adds a pixel to the queue
        Args:
            pixel (Pixel): A Pixel object

        Returns:
            None
        """
        self.queue.append(pixel)

    def __iter__(self):
        """
        Used for iterating through the queue
        Returns:
            queue: The iterator object
        """
        return self

    def __next__(self):
        """
        Gives back the next element in the queue
        Returns:
            The next Pixel in the queue
        Raises:
            StopIteration: If the queue is empty/completed
        """
        if len(self.queue) > 0:
            return self.queue.popleft()
        else:
            raise StopIteration


class Canvas(PixelModule):
    """
    The canvas object
    Attributes:
        config (Config): The configuration object
        _canvas (Canvas): The canvas
        fps (int): The framerate for visual updates
        tasks (Queue): The queue of Pixels
    """

    config: Config
    _canvas: Image
    fps: int = 30
    tasks: Queue
    stats: Stats

    def __init__(self, config: Config):
        """
        Initializes the canvas
        """
        super().__init__("CANVAS")
        self.config = config
        self._canvas = Image.new("RGB", self.config.visuals.size.get_size())
        self.tasks = Queue()

    def stop(self):
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        super().stop()

    def set_stats(self, stats: Stats):
        """
        Sets the stats (initialized after canvas)
        Args:
            stats (Stats): The stats class
        """
        self.stats = stats

    def pixel_in_bounds(self, x: int, y: int) -> bool:
        """
        Checks if the pixel is within the image
        """
        return 0 <= x <= self._canvas.width and 0 <= y <= self._canvas.height

    def get_pixel(self, x: int, y: int) -> Any:
        """
        Gets a single pixel from the canvas
        Args:
            x (int): Coordinate x
            y (int): Coordinate y

        Returns:
            Color
        """
        if self.pixel_in_bounds(x, y):
            return self._canvas.getpixel((x, y))
        else:
            return None

    def add_pixel(self, x: int, y: int, r: int, g: int, b: int, a: int = 255) -> None:
        """
        Adds a single pixel to the queue
        Args:
            x (int): Position x
            y (int): Position y
            r (int): Value Red
            g (int): Value Green
            b (int): Value Blue
            a (int): Value Alpha

        Returns:
            None
        """
        self.tasks.add(Pixel(x, y, r, g, b, a))

    def put_pixel(self, pixel: Pixel):
        """
        Puts a single pixel on the canvas
        Args:
            pixel (Pixel): A pixel (usually from the queue)

        Returns:
            None
        """
        coords, color = pixel.get()
        x, y = coords
        r, g, b, a = color
        if not (
            0 <= x < self.config.visuals.size.width
            and 0 <= y < self.config.visuals.size.height
        ):
            return
        elif pixel.a == 0:
            return
        elif pixel.a == 255:
            self._canvas.putpixel(coords, color)
        else:
            r2, g2, b2, a2 = self._canvas.getpixel(coords)
            r = (r2 * (0xFF - a) + (r * a)) / 0xFF
            g = (g2 * (0xFF - a) + (g * a)) / 0xFF
            b = (b2 * (0xFF - a) + (b * a)) / 0xFF
            self._canvas.putpixel((x, y), (r, g, b))
        self.stats.add_pixel(x, y)

    def get_pixel_color_count(self) -> dict[str, int]:
        """
        Gets a pixel count from the canvas
        Returns:
            A dict with the pixel count
        """
        c = {}
        for x in range(1, self.config.visuals.size.width):
            for y in range(1, self.config.visuals.size.height):
                r, g, b, a = self.get_pixel(x, y)
                if r == g == b == 0:
                    continue
                cString = "#%02x%02x%02x / %d,%d,%d" % (r, g, b, r, g, b)
                if cString in c:
                    c[cString] += 1
                else:
                    c[cString] = 1
        return c

    def get_size(self) -> tuple[int, int]:
        """
        Gets the size of the canvas
        Returns:
            A tuple with the size
        """
        return self.config.visuals.size.get_size()

    def loop(self) -> None:
        """
        The loop for controlling the canvas
        """
        updates = 1.0 / self.fps

        while self.running:
            start = time.time()

            event_handler.trigger("CANVAS-update")

            end = time.time() - start
            gsleep(max(updates - end, 0))

    def update(self):
        """
        Fired by the canvas loop to render queued Pixels
        Returns:
            None
        """
        for pixel in self.tasks:
            self.put_pixel(pixel)

    def get_canvas(self) -> Image:
        """
        Gets a copy of the canvas
        Returns:
            Copy of the canvas
        """
        return self._canvas.copy()

    def is_alive(self) -> bool:
        """
        Gets if the canvas is still alive/rendering
        Returns:
            If the process is alive
        """
        return self.running
