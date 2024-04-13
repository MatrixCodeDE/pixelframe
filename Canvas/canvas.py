import time
from collections import deque
from typing import Any, Callable, Optional

import pygame
from gevent.time import sleep as gsleep
from greenlet import GreenletExit
from PIL import Image
from pygame import Color, Surface, SurfaceType

from Config.config import Config
from Frontend.display import Display
from Frontend.sockets import Socketserver
from Misc.utils import logger
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
        """Returns the Pixel formatted for pygame"""
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


class Canvas(object):
    """
    The canvas object
    Attributes:
        config (Config): The configuration object
        _canvas (Canvas): The canvas
        fps (int): The framerate for visual updates
        kill (bool): The attribute that stops/kills all running processes of the class
        tasks (Queue): The queue of Pixels
        events (dict[str, Callable]): The registered events (usually fired by the Frontend)
        server (Frontend): The socketserver
    """

    config: Config
    _canvas: Image
    display: Display | None
    fps: int = 30
    kill: bool = False
    tasks: Queue
    events: dict[str, Callable]
    socketserver: Socketserver
    stats: Stats

    def __init__(self, config: Config):
        """
        Initializes the canvas
        """
        self.config = config
        self._canvas = Image.new("RGBA", self.config.visuals.size.get_size())
        self.tasks = Queue()
        self.events = {}
        self.pixelcount = 0

        if self.config.frontend.display:
            self.display = Display(self)
        else:
            self.display = None

    def stop(self):
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        self.kill = True
        if self.display:
            self.display.stop()

    def set_socketserver(self, socketserver: Socketserver):
        """
        Sets the server (initialized after canvas) and sets/updates the display's socketserver
        Args:
            socketserver (Socketserver): The socketserver
        """
        self.socketserver = socketserver
        self.display.set_socketserver(self.socketserver)

    def set_stats(self, stats: Stats):
        """
        Sets the stats (initialized after canvas)
        Args:
            stats (Stats): The stats class
        """
        self.stats = stats

    def get_pixel(self, x: int, y: int) -> Color:
        """
        Gets a single pixel from the canvas
        Args:
            x (int): Coordinate x
            y (int): Coordinate y

        Returns:
            Color
        """
        return self._canvas.getpixel((x, y))

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

        while not self.kill:
            start = time.time()

            self.trigger("update")

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

    def register(self, name: str) -> Any:
        """
        Registers a new event for the canvas
        Args:
            name (str): the name for fire the event

        Returns:
            The decorator
        """

        logger.info("Registered event: " + name)

        def decorator(func: Callable) -> Any:
            """
            The decorator for registering events
            Args:
                func (Callable): The function that should be fired

            Returns:
                The function
            """
            self.events[name] = func
            return func

        return decorator

    def trigger(self, name: str, *args, **kwargs) -> None:
        """
        Fires an existing event
        Args:
            name (str): The name of the event
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            None
        """
        if name in self.events:
            try:
                self.events[name](self, *args, **kwargs)
                return True
            except GreenletExit:
                raise
            except:
                logger.exception("Error in callback for %r", name)

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
        return not self.kill
