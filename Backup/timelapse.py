import time
from pathlib import Path

from gevent.time import sleep as gsleep
from PIL import Image

from Canvas.canvas import Canvas
from Config.config import Config
from Misc.utils import logger


class TimelapseHandler:
    config: Config
    canvas: Canvas
    path: Path
    running: bool

    def __init__(self, config: Config, canvas: Canvas) -> None:
        self.config = config
        self.canvas = canvas
        self.setup()
        self.running = True

    def setup(self):
        base = Path().resolve()
        self.path = base / self.config.backup.directory
        if not self.path.exists():
            self.path.mkdir()

    def create_timelapse(self):
        img: Image = self.canvas.get_canvas()
        img = img.convert("RGBA")
        name = time.strftime("image_%Y_%m_%d_%H_%M_%S.png", time.gmtime())
        img.save(self.path / name)

    def stop(self):
        self.running = False

    def loop(self):
        logger.info(f"Starting Process: TIMELAPSE.loop")

        while self.running:
            self.create_timelapse()
            gsleep(self.config.backup.interval)
