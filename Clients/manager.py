from Clients.clients import Client
from Config.config import Config


class Manager:
    """
    The manager class that manages all connections with clients within the current session
    Attributes:
        config (Config): The configuration
        clients (dict): A dictionary with all the clients that ever connected to the server
    """

    config: Config | None
    clients: dict[str, Client]

    def __init__(self):
        self.config = None
        self.clients = {}

    def set_config(self, config: Config):
        """
        Sets the configuration
        """
        self.config = config

    def add_client(self, ip: str):
        """
        Adds a new client
        """
        client = Client(self.config, ip)
        self.clients[str(client)] = client
        return client

    def ensure_client(self, ip: str):
        """
        Ensures a client exists
        """
        if ip not in self.clients:
            self.add_client(ip)

    def client(self, ip: str):
        """
        Returns the client with the given ip
        """
        self.ensure_client(ip)
        return self.clients[ip]

    def connect_client(self, ip: str):
        """
        Triggered if a netcat connection is established
        """
        self.ensure_client(ip)
        self.clients[ip].connect()

    def disconnect_client(self, ip: str):
        """
        Triggered if a netcat connection is lost
        """
        self.ensure_client(ip)
        self.clients[ip].disconnect()


manager = Manager()
