import time
from typing import Optional

from gevent import spawn
from gevent._socket3 import socket as socket3
from gevent.lock import RLock

from Config.config import Config
from Misc.utils import logger


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
    canvas: Optional["Canvas"]
    socket: socket3 | None
    connected: bool = False
    connected_at: float
    cooldown: float
    cooldown_until: float
    lock: RLock
    kill: bool = False
    timeout: bool

    def __init__(
        self, canvas: Optional["Canvas"], ip: str, port: int, pps: int | float = 30
    ) -> None:
        """
        Initializes the client object
        Args:
            canvas (Canvas): The canvas
            ip (str): The IP address of the client
            port (int): The port of the client
            pps (int): The number of pixels a client can set per second
        """
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
                        if not self.canvas.trigger(
                            "COMMAND-%s" % command.upper(), self, *arguments
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
                    if not self.canvas.trigger(
                        "COMMAND-%s" % command.upper(), self, *arguments
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


class Socketserver(object):
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
        kill (bool): The attribute that stops/kills all running processes of the class
    """

    config: Config
    canvas: Optional["Canvas"]
    host: str
    port: int
    socket: socket3
    clients: dict[str, Client]
    cpps: int | float
    kill: bool = False

    def __init__(self, canvas: Optional["Canvas"], config: Config) -> None:
        """
        Initializes the server
        Args:
            canvas (Canvas): The canvas object
            config (Config): The config object
        """
        self.config = config
        self.canvas = canvas
        self.host = self.config.connection.host
        self.port = self.config.connection.port
        self.socket = socket3()
        self.socket.bind((self.config.connection.host, self.config.connection.port))
        self.socket.listen()
        self.clients = {}
        self.canvas.set_server(self)

    def stop(self) -> None:
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        clients = self.clients.values()
        for client in clients:
            client.stop()
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
