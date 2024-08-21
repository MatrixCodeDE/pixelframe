import json
import time

from Misc.utils import NoFrontendException, confirm, logger


class General(object):
    name: str

    def __init__(self, name: str):
        self.name = name


class Display:
    enabled: bool
    fps: int

    def __init__(self, enabled: bool, fps: int):
        self.enabled = enabled
        self.fps = fps
        if self.fps > 10:
            logger.warn("Display FPS > 10 can result in major performance problems!")
            time.sleep(0.1)  # To make sure logger message was sent
            confirm()


class Api:
    enabled: bool
    enable_admin: bool

    def __init__(self, enabled: bool, enable_admin: bool):
        self.enabled = enabled
        self.enable_admin = enable_admin


class Sockets:
    enabled: bool
    enable_admin: bool

    def __init__(self, enabled: bool, enable_admin: bool):
        self.enabled = enabled
        self.enable_admin = enable_admin


class Web:
    force_reload: bool

    def __init__(self, force_reload: bool):
        self.force_reload = force_reload


class Frontend:
    display: Display
    api: Api
    sockets: Sockets
    web: Web

    def __init__(self, display: dict, api: dict, sockets: dict, web: dict):
        self.display = Display(**display)
        self.api = Api(**api)
        self.sockets = Sockets(**sockets)
        self.web = Web(**web)
        if not self.display.enabled and not self.api.enabled:
            raise NoFrontendException()


class Ports:
    socket: int
    api: int

    def __init__(self, socket: int, api: int):
        self.socket = socket
        self.api = api


class Connection(object):
    host: str
    ports: Ports
    timeout: int

    def __init__(self, host: str, ports: dict, timeout: int):
        self.host = host
        self.ports = Ports(**ports)
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
    debug: bool
    general: General
    frontend: Frontend
    connection: Connection
    visuals: Visuals
    game: Game

    def __init__(self, config_file: str, debug: bool = False):
        self.config_file = config_file
        self.debug = debug
        self.load_config()

    def read_config(self) -> dict:
        with open(self.config_file, "r") as f:
            conf = json.load(f)
        return conf

    def load_config(self):
        try:
            conf = self.read_config()
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
