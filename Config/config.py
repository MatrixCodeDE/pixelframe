import json
from typing import Any


class General(object):
    name: str

    def __init__(self, name: str):
        self.name = name


class Frontend:
    display: bool

    def __init__(self, display: bool):
        self.display = display


class Connection(object):
    host: str
    port: int
    timeout: int

    def __init__(self, host: str, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout


class Size(object):
    width: int
    height: int

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def get_size(self) -> tuple[int, int]:
        return self.width, self.height


class StatsBar:
    enabled: bool
    size: int

    def __init__(self, enabled: bool, size: int):
        self.enabled = enabled
        self.size = size


class Visuals(object):
    size: Size
    statsbar: StatsBar

    def __init__(self, size: dict, statsbar: dict):
        self.size = Size(**size)
        self.statsbar = StatsBar(**statsbar)


class Godmode(object):
    enabled: bool
    pps: int | float

    def __init__(self, enabled: bool, pps: int | float):
        self.enabled = enabled
        self.pps = pps


class Game(object):
    pps: int | float
    godmode: Godmode

    def __init__(self, pps: int | float, godmode: dict):
        self.pps = pps
        self.godmode = Godmode(**godmode)


class Config(object):
    config_file: str
    general: General
    frontend: Frontend
    connection: Connection
    visuals: Visuals
    game: Game

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.load_config()

    def get_config(self) -> dict:
        with open(self.config_file, "r") as f:
            conf = json.load(f)
        return conf

    def load_config(self):
        try:
            conf = self.get_config()
            self.general = General(**conf["general"])
            self.frontend = Frontend(**conf["frontend"])
            self.connection = Connection(**conf["connection"])
            self.visuals = Visuals(**conf["visuals"])
            self.game = Game(**conf["game"])
        except FileNotFoundError as fe:
            raise FileNotFoundError(
                f"The provided Config file was not found: {fe.filename}"
            )
        except TypeError as te:
            raise TypeError(f"The provided Config file is malformed: {te.args}")
