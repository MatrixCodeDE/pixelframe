import logging
import time
from collections import deque

from typing import Callable, Any, Optional
import pygame
from gevent import spawn
from gevent._socket3 import socket as socket3
from gevent.lock import RLock
from gevent.time import sleep as gsleep
from greenlet import GreenletExit
from pygame import Surface, SurfaceType, Color

logger = logging.getLogger("pixelframe")
logging.basicConfig(level=logging.DEBUG)


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
        size (tuple[int, int]): The size of the canvas
        flags (int): Flags for pygame
        screen (Surface | SurfaceType): The pygame screen
        fps (int): The framerate for visual updates
        kill (bool): The attribute that stops/kills all running processes of the class
        tasks (Queue): The queue of Pixels
        events (dict[str, Callable]): The registered events (usually fired by the Server)
        stats (bool): Turns on/off the statistics on top of the canvas
    """
    size: tuple[int, int] = 500, 500
    flags: int = pygame.SCALED | pygame.RESIZABLE
    screen: Surface | SurfaceType
    fps: int = 30
    kill: bool = False
    tasks: Queue
    events: dict[str, Callable]
    stats_size: tuple[int, int]
    server: Optional["Server"] | None
    pixelcount: int

    def __init__(self, size: tuple[int, int] = None, stats_size: tuple[int, int] = None):
        """
        Initializes the canvas
        """
        pygame.init()
        pygame.mixer.quit()
        pygame.display.set_caption("PixelFrame")
        pygame.font.init()
        if size:
            self.size = size
        if not stats_size:
            self.stats_size = 0, 0
        else:
            if stats_size[0] < 0 or stats_size[1] < 0:
                raise Exception("Invalid stats size")
        self.stats_size = stats_size
        self.screen = pygame.display.set_mode(self.size, self.flags)
        self.tasks = Queue()
        self.events = {}
        self.server = None
        self.pixelcount = 0

    def stop(self):
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        self.kill = True
        pygame.quit()

    def set_server(self, server: Optional["Server"]):
        self.server = server

    def get_pixel(self, x: int, y: int) -> Color:
        """
        Gets a single pixel from the canvas
        Args:
            x (int): Coordinate x
            y (int): Coordinate y

        Returns:
            Color
        """
        return self.screen.get_at(self.translate_position(x, y))

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
        x, y = self.translate_position(x, y)
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
        if not (0 <= x < self.size[0] and 0 <= y < self.size[1]):
            return
        elif pixel.a == 0:
            return
        elif pixel.a == 255:
            self.screen.set_at(coords, color)
        else:
            r2, g2, b2, a2 = self.screen.get_at((x, y))
            r = (r2 * (0xFF - a) + (r * a)) / 0xFF
            g = (g2 * (0xFF - a) + (g * a)) / 0xFF
            b = (b2 * (0xFF - a) + (b * a)) / 0xFF
            self.screen.set_at((x, y), (r, g, b))
        self.pixelcount += 1

    def get_pixel_color_count(self) -> dict[str, int]:
        """
        Gets a pixel count from the canvas
        Returns:
            A dict with the pixel count
        """
        c = {}
        for x in range(1, self.size[0]):
            for y in range(1, self.size[1]):
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
        if not self.stats:
            return self.size
        else:
            return self.size[0], self.size[1] - 40

    def loop(self) -> None:
        """
        The loop for controlling the canvas
        """
        updates = 1.0 / self.fps
        flip = pygame.display.flip

        while not self.kill:
            start = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.trigger("stop")
                    return
                elif event.type == pygame.KEYDOWN:
                    self.trigger("KEYDOWN-" + event.unicode)

            self.trigger("render")
            flip()

            end = time.time() - start
            gsleep(max(updates - end, 0))

    def render(self):
        """
        Fired by the canvas loop to render queued Pixels
        Returns:
            None
        """
        for pixel in self.tasks:
            self.put_pixel(pixel)
        if self.stats_size[0] > 0:
            self.render_stats()

    def render_stats(self):
        if not self.server:
            return
        users: int = self.server.user_count()
        pixel: int = self.pixelcount

        text: str = f"Host: {self.server.host} | Port: {self.server.port} | Users: {users} | Pixels: {pixel}"
        font = pygame.font.SysFont("monospace", self.stats_size[1])
        rendertext = font.render(text, True, (255, 255, 255))
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, self.size[0], self.stats_size[0]))
        tsx, tsy = font.size(text)
        self.screen.blit(rendertext, (self.size[0]/2 - tsx/2, self.stats_size[0]/2 - tsy/2))

    def translate_position(self, x: int, y: int) -> tuple[int, int]:
        if self.stats_size[0] == 0:
            return x, y
        return x, y + self.stats_size[0]

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

    def is_alive(self) -> bool:
        """
        Gets of the canvas is still alive/rendering
        Returns:
            If the process is alive
        """
        return not self.kill


class Client:
    """
    The client object (used for the server)
    Attributes:
        pps (int): The number of pixels per second a user can set
        ip (str): The IP address of the client
        canvas (Canvas): The canvas object
        socket (socket): The socket the client is connected to
        connected (bool): Whether the client is currently connected to the server
        connected_at (float): The unix time the client has connected
        cooldown (float): The cooldown for each pixel (calculated by the pps)
        cooldown_until(float): The unix time when the client can place the next pixel
        lock (RLock): The locking primative to identify the Greenlet
        kill (bool): The attribute that stops/kills all running processes of the class

    """
    pps: int | float = 10  # Pixel per Second
    ip: str
    port: int
    canvas: Canvas
    socket: socket3 | None
    connected: bool = False
    connected_at: float
    cooldown: float = 1.0 / pps
    cooldown_until: float
    lock: RLock
    kill: bool = False

    def __init__(self, canvas: Canvas, ip: str, port: int) -> None:
        """
        Initializes the client object
        Args:
            canvas (Canvas): The canvas
            ip (str): The IP address of the client
            port (int): The port of the client
        """
        self.canvas = canvas
        self.ip = ip
        self.port = port
        self.socket = None
        self.connected_at = time.time()
        self.cooldown_until = 0
        self.lock = RLock()

    def stop(self) -> None:
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        self.kill = True

    def send(self, line: str) -> None:
        """
        Sends a line to the client socket
        Args:
            line (str): The line to send

        Returns:
            None
        """
        with self.lock:
            if self.socket:
                self.socket.sendall((line + "\n").encode())

    def nospam(self, line: str) -> None:
        """
        Sends a nospam line to the client socket
        Args:
            line (str): The line to send

        Returns:
            None
        """
        self.send(line)

    def connect(self, socket: socket3) -> None:
        """
        The 'loop' for handling the client connection
        Args:
            socket (socket): the socket of the client
        """
        self.socket = socket
        self.connected = True

        with self.lock:
            self.socket = socket
            readline = self.socket.makefile().readline

        try:
            while self.socket and not self.kill:
                line = ""
                while not self.kill:
                    line = readline(1024).strip()
                    if not line:
                        self.disconnect()
                    break
                arguments = line.split()
                if not arguments:
                    self.disconnect()
                    break
                command = arguments.pop(0)

                if command == "PX" and len(arguments) != 2:
                    now = time.time()
                    cd = self.cooldown_until - now
                    if cd < 0:
                        if not self.canvas.trigger(
                                "COMMAND-%s" % command.upper(), self, *arguments
                        ):
                            self.send("Wrong arguments")
                        self.cooldown_until = now + self.cooldown

                    else:
                        if cd >= 1.0:
                            self.nospam(f"You are on cooldown for {cd:.2f} seconds")
                        else:
                            self.nospam(f"You are on cooldown for {cd*1000:.2f} milliseconds")

                else:
                    if not self.canvas.trigger(
                            "COMMAND-%s" % command.upper(), self, *arguments
                    ):
                        self.send("Wrong arguments")
        finally:
            self.disconnect()

    def disconnect(self) -> None:
        """
        Disconnects the client and closes the socket
        Returns:
            None
        """
        with self.lock:
            if self.socket:
                socket = self.socket
                self.socket = None
                socket.close()
                self.connected = False


class Server(object):
    """
    The socketserver for handling client sockets
    Attributes:
        canvas (Canvas): The canvas object
        host (str): The host address of the server
        port (int): The port of the server
        socket(socket): The socket server
        clients (dict[str, Client]): The list of clients
        kill (bool): The attribute that stops/kills all running processes of the class
    """
    canvas: Canvas
    host: str
    port: int
    socket: socket3
    clients: dict[str, Client]
    kill: bool = False

    def __init__(self, canvas: Canvas, host: str, port: int) -> None:
        """
        Initializes the server
        Args:
            canvas (Canvas): The canvas object
            host (str): The host address of the server
            port (int): The port of the serve
        """
        self.canvas = canvas
        self.host = host
        self.port = port
        self.socket = socket3()
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.clients = {}

    def stop(self) -> None:
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        for client in self.clients.values():
            client.stop()
            del self.clients[client.ip]
        self.kill = True

    def loop(self):
        """
        The loop for handling the client connections
        """
        while not self.kill:
            sock, addr = self.socket.accept()
            ip, port = addr

            client: Client = self.clients.get(ip)
            if client:
                client.disconnect()
                client.task.kill()
            else:
                client = self.clients[ip] = Client(self.canvas, ip, port)

            client.task = spawn(client.connect, sock)

    def user_count(self):
        connected = [client for client in self.clients.values() if client.connected]
        return len(connected)


def register_events(canvas: Canvas) -> None:
    """
    Registers the needed events for the server
    Args:
        canvas (Canvas): The canvas object

    Returns:
        None
    """

    logger.info("Registering events")

    @canvas.register("render")
    def render(canvas: Canvas):
        canvas.render()

    @canvas.register("stop")
    def stop(canvas: Canvas):
        canvas.stop()

    @canvas.register("COMMAND-PX")
    def add_pixel(canvas: Canvas, client: Client, x, y, color=None):
        x, y = int(x), int(y)
        if color:
            c = int(color, 16)
            if len(color) == 6:
                r = (c & 0xFF0000) >> 16
                g = (c & 0x00FF00) >> 8
                b = c & 0x0000FF
                a = 0xFF
            elif len(color) == 8:
                r = (c & 0xFF000000) >> 24
                g = (c & 0x00FF0000) >> 16
                b = (c & 0x0000FF00) >> 8
                a = c & 0x000000FF
            else:
                return
            canvas.add_pixel(x, y, r, g, b, a)
        else:
            r, g, b, a = canvas.get_pixel(x, y)
            client.send("PX %d %d %02x%02x%02x%02x" % (x, y, r, g, b, a))

    @canvas.register("COMMAND-HELP")
    def on_help(canvas: Canvas, client: Client):
        help = "Commands:\n"
        help += ">>> HELP\n"
        help += ">>> STATS\n"
        help += ">>> SIZE\n"
        help += ">>> QUIT\n"
        help += ">>> TEXT x y text (currently disabled)\n"
        help += ">>> PX x y [RRGGBB[AA]]\n"
        client.send(help)

    @canvas.register("COMMAND-STATS")
    def callback(canvas: Canvas, client: Client):
        d = canvas.get_pixel_color_count()
        import operator

        dSorted = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        dString = ""
        for k, v in dSorted:
            dString += str(k) + ":\t" + str(v) + "\n"
        client.send("Current pixel color distribution:\n" + dString)

    # @canvas.register("COMMAND-TEXT")
    def on_text(canvas: Canvas, client: Client, x, y, *words):
        x, y = int(x), int(y)
        text = " ".join(words)[:200]
        canvas.text(x, y, text, delay=1)

    @canvas.register("COMMAND-SIZE")
    def on_size(canvas: Canvas, client: Client):
        client.send("SIZE %d %d" % canvas.get_size())

    @canvas.register("COMMAND-QUIT")
    def on_quit(canvas: Canvas, client: Client):
        client.disconnect()

    # @canvas.register("COMMAND-GODMODE")
    def on_quit(canvas: Canvas, client: Client, mode):
        if mode == "on":
            client.pps = 100000
            client.send("You are now god (%d pps)" % client.pps)
        else:
            client.pps = 100
            client.send("You are no longer god (%d pps)" % client.pps)

    logger.info("Successfully registered Events")


def main():
    """
    The main function of PixelFrame
    """
    canvas = Canvas((1920, 1080), (40, 30))

    register_events(canvas)

    logger.info("Starting Canvas Loop")
    main_loop = spawn(canvas.loop)
    main_loop.start()

    server = Server(canvas, "0.0.0.0", 1234)
    canvas.set_server(server)

    logger.info(f"Starting Server at {server.host}:{server.port}")
    server_loop = spawn(server.loop)

    try:
        server_loop.join()
    except KeyboardInterrupt:
        print("Exitting...")
    canvas.stop()
    server.stop()
    main_loop.kill()
    server_loop.kill()


if __name__ == "__main__":
    main()
