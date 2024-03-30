import logging
import time
from collections import deque

import pygame
from gevent import spawn
from gevent._socket3 import socket
from gevent.lock import RLock
from gevent.time import sleep as gsleep
from greenlet import GreenletExit
from pygame import Surface, SurfaceType

logger = logging.getLogger("pixelframe")
logging.basicConfig(level=logging.DEBUG)


class Pixel(object):
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
    queue: deque

    def __init__(self):
        self.queue = deque()

    def add(self, pixel: Pixel):
        self.queue.append(pixel)

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.queue) > 0:
            return self.queue.popleft()
        else:
            raise StopIteration


class Canvas(object):
    size: tuple[int, int] = 500, 500
    flags: int = pygame.SCALED | pygame.RESIZABLE
    screen: Surface | SurfaceType
    fps = 30
    kill: bool = False
    tasks: Queue
    events: dict

    def __init__(self):
        pygame.init()
        pygame.mixer.quit()
        pygame.display.set_caption("PixelFrame")
        self.screen = pygame.display.set_mode(self.size, self.flags)
        self.tasks = Queue()
        self.events = {}

    def stop(self):
        self.kill = True
        pygame.quit()

    def get_pixel(self, x, y):
        return self.screen.get_at((x, y))

    def add_pixel(self, x: int, y: int, r: int, g: int, b: int, a: int = 255):
        self.tasks.add(Pixel(x, y, r, g, b, a))

    def put_pixel(self, pixel: Pixel):
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

    def get_pixel_color_count(self):
        c = {}
        for x in range(1, self.width):
            for y in range(1, self.height):
                r, g, b, a = self.get_pixel(x, y)
                if r == g == b:
                    continue
                cString = "#%02x%02x%02x / %d,%d,%d" % (r, g, b, r, g, b)
                if cString in c:
                    c[cString] += 1
                else:
                    c[cString] = 1
        return c

    def get_size(self):
        return self.size

    def loop(self):
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
        for pixel in self.tasks:
            self.put_pixel(pixel)

    def register(self, name):
        """Register a new event"""

        logger.info("Registered event: " + name)

        def decorator(func):
            self.events[name] = func
            return func

        return decorator

    def trigger(self, name, *args, **kwargs):
        """Trigger an existing event"""
        if name in self.events:
            try:
                self.events[name](self, *args, **kwargs)
                return True
            except GreenletExit:
                raise
            except:
                logger.exception("Error in callback for %r", name)

    def is_alive(self):
        return not self.kill


class Client:
    pps = 10  # Pixel per Second

    ip: str
    canvas: Canvas
    socket: socket | None
    connected_at: float
    cooldown: 1.0 / pps
    cooldown_until: float
    lock: RLock
    kill: bool = False

    def __init__(self, canvas, ip):
        self.canvas = canvas
        self.ip = ip
        self.socket = None
        self.connected_at = time.time()
        self.cooldown_until = 0
        self.lock = RLock()

    def stop(self):
        self.kill = True

    def send(self, line):
        with self.lock:
            if self.socket:
                self.socket.sendall((line + "\n").encode())

    def nospam(self, line):
        self.send(line)

    def connect(self, socket):
        self.socket = socket

        with self.lock:
            self.socket = socket
            readline = self.socket.makefile().readline

        try:
            """line = ""
            while not self.kill:
                c = readline(1)
                if "\n" == c or not c:
                    break
                line += c
            if not line:
                raise
            arguments = line.split()
            command = arguments.pop(0)

            if command == "PX" and len(arguments) != 2:
                now = time.time()
                cd = self.cooldown_until - now
                if cd < 0:
                    if not self.canvas.trigger(
                        "COMMAND-%s" % command.upper(), self, *arguments
                    ):
                        self.send("Wrong arguments")

                else:
                    self.nospam(f"You are on cooldown for {cd} seconds")
                    gsleep(cd)

            else:
                if not self.canvas.trigger(
                    "COMMAND-%s" % command.upper(), self, *arguments
                ):
                    self.send("Wrong arguments")"""
            while self.socket:
                gsleep(10.0 / self.pps)
                for i in range(10):
                    line = readline(1024).strip()
                    if not line:
                        break
                    arguments = line.split()
                    command = arguments.pop(0)
                    if not self.canvas.trigger('COMMAND-%s' % command.upper(), self, *arguments):
                        self.disconnect()
        finally:
            self.disconnect()

    def disconnect(self):
        with self.lock:
            if self.socket:
                socket = self.socket
                self.socket = None
                socket.close()


class Server(object):
    canvas: Canvas
    host: str
    port: int
    socket: socket
    clients: dict
    kill: bool = False

    def __init__(self, canvas, host, port):
        self.canvas = canvas
        self.host = host
        self.port = port
        self.socket = socket()
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.clients = {}

    def stop(self):
        self.kill = True

    def loop(self):
        while not self.kill:
            sock, addr = self.socket.accept()
            ip, port = addr

            client: Client = self.clients.get(ip)
            if client:
                client.disconnect()
                client.task.kill()
            else:
                client = self.clients[ip] = Client(self.canvas, ip)

            client.task = spawn(client.connect, sock)


def register_events(canvas: Canvas):
    """Register all events"""

    logger.info("Registering events")

    @canvas.register("render")
    def render(canvas: Canvas):
        canvas.render()

    @canvas.register("stop")
    def stop(canvas: Canvas):
        canvas.stop()

    @canvas.register("COMMAND-PX")
    def add_pixel(canvas: Canvas, client: Client, x, y, color=None):
        global pixelcount
        pixelcount += 1
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


def maintainer(canvas: Canvas, client: Client):
    while canvas.is_alive():
        pass


def main():
    global pixelcount
    pixelcount = 0
    canvas = Canvas()

    register_events(canvas)

    logger.info("Starting Canvas Loop")
    main_loop = spawn(canvas.loop)
    main_loop.start()

    server = Server(canvas, "0.0.0.0", 1234)

    logger.info(f"Starting Server at {server.host}:{server.port}")
    server_loop = spawn(server.loop)
    server_loop.join()

    try:
        while canvas.is_alive():
            pass
        print("eixt")
    except KeyboardInterrupt:
        print("Exitting...")
    main_loop.kill()
    server_loop.kill()


if __name__ == "__main__":
    main()
