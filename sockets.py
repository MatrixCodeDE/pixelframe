import time

from gevent import spawn
from gevent._socket3 import socket as socket3
from gevent.lock import RLock

from canvas import Canvas


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
        clients = self.clients.values()
        for client in clients:
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