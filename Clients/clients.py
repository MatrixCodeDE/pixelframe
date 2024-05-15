import time

from Config.config import Config


class Client:

    config: Config
    connected: bool
    pps: float
    last_update: float
    ip: str
    god: bool

    def __init__(self, config: Config, ip: str):
        self.config = config
        self.ip = ip
        self.connected = False
        self.pps = config.game.pps
        self.last_update = 0
        self.god = False

    def __str__(self):
        return self.ip

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def godmode(self, god: bool):
        self.god = god
        if god:
            self.pps = self.config.game.godmode.pps
        else:
            self.pps = self.config.game.pps

    def update_cooldown(self):
        self.last_update = time.time()

    def on_cooldown(self) -> float:
        if self.god:
            return 0
        delta = self.last_update + (1 / self.pps) - time.time()
        if delta > 0:
            return delta
        return 0
