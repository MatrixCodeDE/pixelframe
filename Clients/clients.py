import time

from Config.config import Config


class Client:
    """
    All Interactions with the server are handled with this class.
    Attributes:
        config (Config): The configuration
        connected (bool): If the client is connected (NC only)
        pps (float): The amoun of pixels the client can set per second
        last_update (float): The last update of a pixel
        ip (str): The IP address of the client
        god (bool): If the client has godmode allowed (more features)
    """
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
        """
        Returns a string representation of the client as the client's IP address'
        """
        return self.ip

    def connect(self):
        """Sets the state connected to true"""
        self.connected = True

    def disconnect(self):
        """Sets the state connected to false"""
        self.connected = False

    def godmode(self, god: bool):
        """
        Toggles godmode for the client
        """
        self.god = god
        if god:
            self.pps = self.config.game.godmode.pps
        else:
            self.pps = self.config.game.pps

    def update_cooldown(self):
        """
        Updates the last pixel update to current time
        """
        self.last_update = time.time()

    def on_cooldown(self) -> float:
        """
        Returns the seconds the client has to wait until next update
        """
        if self.god:
            return 0
        delta = self.last_update + (1 / self.pps) - time.time()
        if delta > 0:
            return delta
        return 0
