import json
import logging
import time
from json import JSONDecodeError

from Misc.errors import MalformedConfigError, NoConfigError
from Misc.utils import NoFrontendException, confirm, logger


class General(object):
    name: str
    version: str

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version


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


class Backup(object):
    enabled: bool
    interval: int
    directory: str
    delete: int

    def __init__(self, enabled: bool, interval: int, directory: str, delete: int):
        self.enabled = enabled
        self.interval = interval
        self.directory = directory
        self.delete = delete


class Logging(object):
    """
    Logging Config
    When started with debug flag, the logging level is forced to 0/Debug
    Attributes:
        level (int): 0 = Debug, 1 = Info, 2 = Warning, 3 = Error, 4 = Critical
        loglevel (int): representing the correct loglevel from logging module
    """

    level: int
    loglevel: int

    _levelmapping = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.CRITICAL,
        logging.DEBUG: logging.DEBUG,
        logging.INFO: logging.INFO,
        logging.WARNING: logging.WARNING,
        logging.ERROR: logging.ERROR,
        logging.CRITICAL: logging.CRITICAL,
    }

    def __init__(self, level: int, *, debug: bool = None):
        if debug:
            level = 0
        if level not in self._levelmapping:
            raise MalformedConfigError(
                "config.json"
                "logging.level must be between 0 (Debug) and 3 (Critical)"
            )
        self.level = level
        self.loglevel = self._levelmapping[level]


class Timelapse(object):
    enabled: bool
    interval: int
    directory: str

    def __init__(self, enabled: bool, interval: int, directory: str):
        self.enabled = enabled
        self.interval = interval
        self.directory = directory


class Config(object):
    config_file: str
    debug: bool

    backup: Backup
    connection: Connection
    frontend: Frontend
    game: Game
    general: General
    logging: Logging
    timelapse: Timelapse
    visuals: Visuals

    def __init__(self, config_file: str, debug: bool = False):
        self.config_file = config_file
        self.debug = debug
        self.load_config()
        if self.debug:
            self.logging.level = 0

    def read_config(self) -> dict:
        with open(self.config_file, "r") as f:
            conf = json.load(f)
        return conf

    def load_config(self):
        try:
            conf = self.read_config()
            self.backup = Backup(**conf["backup"])
            self.connection = Connection(**conf["connection"])
            self.frontend = Frontend(**conf["frontend"])
            self.general = General(**conf["general"])
            self.game = Game(**conf["game"])
            self.logging = Logging(**conf["logging"], debug=self.debug)
            self.timelapse = Timelapse(**conf["timelapse"])
            self.visuals = Visuals(**conf["visuals"])
        except FileNotFoundError as fe:
            raise NoConfigError(fe.filename)
        except (TypeError, JSONDecodeError) as te:
            raise MalformedConfigError(te.args)

    def reload(self):
        self.load_config()
