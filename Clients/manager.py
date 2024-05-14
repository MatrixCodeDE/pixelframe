from Clients.clients import Client
from Config.config import Config


class Manager:
    config: Config | None
    clients: dict[str, Client]

    def __init__(self):
        self.config = None
        self.clients = {}

    def set_config(self, config: Config):
        self.config = config

    def add_client(self, ip: str):
        client = Client(self.config, ip=ip)
        self.clients[str(client)] = client
        return client

    def ensure_client(self, ip: str):
        if ip not in self.clients:
            self.add_client(ip)

    def client(self, ip: str):
        self.ensure_client(ip)
        return self.clients[ip]

    def connect_client(self, ip: str):
        self.ensure_client(ip)
        self.clients[ip].connect()

    def disconnect_client(self, ip: str):
        self.ensure_client(ip)
        self.clients[ip].disconnect()


manager = Manager()
