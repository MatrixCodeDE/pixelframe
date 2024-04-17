import time
from typing import Optional

from gevent import spawn
from gevent._socket3 import socket as socket3
from gevent.lock import RLock

from Canvas.canvas import Canvas
from Config.config import Config
from Misc.Template.pixelmodule import PixelModule
from Misc.utils import event_handler, logger


class Client:
    """
    The client object (used for the server)
    Attributes:
        pps (int): The number of pixels a client can set per second
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

    pps: int | float  # Pixel per Second
    ip: str
    port: int
    canvas: Canvas
    socket: socket3 | None
    connected: bool = False
    connected_at: float
    cooldown: float
    cooldown_until: float
    lock: RLock
    kill: bool = False
    timeout: bool

    def __init__(
        self, canvas: Optional["Canvas"], ip: str, port: int, pps: int | float = 30, super_prefix: str = "SOCKSERV"
    ) -> None:
        """
        Initializes the client object
        Args:
            canvas (Canvas): The canvas
            ip (str): The IP address of the client
            port (int): The port of the client
            pps (int): The number of pixels a client can set per second
        """
        self.super_prefix = super_prefix
        self.canvas = canvas
        self.ip = ip
        self.port = port
        self.pps = pps
        self.cooldown = 1.0 / self.pps
        self.socket = None
        self.connected_at = time.time()
        self.cooldown_until = 0
        self.lock = RLock()
        self.timeout = False

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
                try:
                    self.socket.sendall(("> " + line + "\n").encode())
                except BrokenPipeError as e:
                    logger.error(e)

    def set_pps(self, pps: int | float) -> None:
        self.pps = pps
        self.cooldown = 1.0 / self.pps

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
        self.kill = False
        self.socket.settimeout(self.canvas.config.connection.timeout)
        self.connected = True

        logger.info(f"Client connected: {self.ip}:{self.port}")

        with self.lock:
            self.socket = socket
            readline = self.socket.makefile().readline

        try:
            while self.socket and not self.kill:
                line = ""
                while not self.kill:
                    try:
                        line = readline(1024).strip()
                    except (ConnectionResetError, TimeoutError):
                        self.stop()
                        return
                    if not line:
                        self.disconnect()
                        return
                    break
                arguments = line.split()
                if not arguments:
                    self.disconnect()
                    return
                command = arguments.pop(0).upper()

                if command == "PX" and len(arguments) != 2:
                    now = time.time()
                    cd = self.cooldown_until - now
                    if cd < 0:
                        if not event_handler.trigger(
                            f"{self.super_prefix}-%s" % command.upper(), self, *arguments
                        ):
                            self.send("Wrong arguments")
                        self.cooldown_until = now + self.cooldown

                    else:
                        if cd >= 1.0:
                            self.nospam(f"You are on cooldown for {cd:.2f} seconds")
                        else:
                            self.nospam(
                                f"You are on cooldown for {cd*1000:.2f} milliseconds"
                            )

                else:
                    if not event_handler.trigger(
                        f"{self.super_prefix}-%s" % command.upper(), self, *arguments
                    ):
                        self.send("Wrong arguments")
        finally:
            self.send("Connection Timeout...")
            self.timeout = True
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
                if self.timeout:
                    self.send("Disconnected")
                else:
                    self.send(
                        "You were disconnected due to another connection with your IP address."
                    )
                socket.close()
                self.socket = None
                self.connected = False
                logger.info(f"Client disconnected: {self.ip}:{self.port}")


class Socketserver(PixelModule):
    """
    The socketserver for handling client sockets
    Attributes:
        canvas (Canvas): The canvas object
        config (Config): The config object
        host (str): The host address of the server
        port (int): The port of the server
        socket(socket): The socket server
        clients (dict[str, Client]): The list of clients
        cpps (int | float): Refers to default pps of the clients
    """

    config: Config
    canvas: Canvas
    host: str
    port: int
    socket: socket3
    clients: dict[str, Client]
    cpps: int | float

    def __init__(self, canvas: Canvas, config: Config) -> None:
        """
        Initializes the server
        Args:
            canvas (Canvas): The canvas object
            config (Config): The config object
        """
        self.config = config
        self.canvas = canvas
        self.host = self.config.connection.host
        self.port = self.config.connection.ports.socket
        self.socket = socket3()
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.clients = {}
        super().__init__("SOCKSERV")

    def stop(self) -> None:
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        clients = self.clients.values()
        for client in clients:
            client.stop()

    def loop(self):
        """
        The loop for handling the client connections
        """
        logger.info(f"Starting Process: {self.name}.loop")
        while self.running:
            sock, addr = self.socket.accept()
            ip, port = addr

            client: Client = self.clients.get(ip)
            if client:
                client.disconnect()
                client.task.kill()
            else:
                client = self.clients[ip] = Client(
                    self.canvas, ip, port, self.config.game.pps
                )

            client.task = spawn(client.connect, sock)

    def user_count(self) -> int:
        """
        Returns the number of connected clients
        Returns:
            int: number of connected clients
        """
        connected = [client for client in self.clients.values() if client.connected]
        return len(connected)

    def register_events(self):
        super().register_events()

        @event_handler.register(f"{self.name}-PX")
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
                client.send("PX Success")
            else:
                r, g, b = canvas.get_pixel(x, y)
                client.send("PX %d %d %02x%02x%02x" % (x, y, r, g, b))

        @event_handler.register(f"{self.name}-HELP")
        def on_help(canvas: Canvas, client: Client):
            help = "Commands:\n"
            help += ">>> HELP\n"
            help += ">>> STATS\n"
            help += ">>> SIZE\n"
            help += ">>> QUIT\n"
            # help += ">>> TEXT x y text (currently disabled)\n"
            help += ">>> PX x y [RRGGBB[AA]]\n"
            help += f"Pixel per second per user: {client.pps}"
            client.send(help)

        @event_handler.register(f"{self.name}-STATS")
        def callback(canvas: Canvas, client: Client):
            d = canvas.get_pixel_color_count()
            import operator

            dSorted = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
            dString = ""
            for k, v in dSorted:
                dString += str(k) + ":\t" + str(v) + "\n"
            client.send("Current pixel color distribution:\n" + dString)

        @event_handler.register(f"{self.name}-SIZE")
        def on_size(canvas: Canvas, client: Client):
            client.send("SIZE %d %d" % canvas.get_size())

        @event_handler.register(f"{self.name}-EXIT")
        def on_quit(canvas: Canvas, client: Client):
            client.disconnect()

        if self.config.game.godmode.enabled:
            @event_handler.register(f"{self.name}-GODMODE")
            def on_quit(canvas: Canvas, client: Client, mode):
                if mode == "on":
                    client.set_pps(self.config.game.godmode.pps)
                    client.send("You are now god (%d pps)" % client.pps)
                else:
                    client.set_pps(self.config.game.pps)
                    client.send("You are no longer god (%d pps)" % client.pps)

