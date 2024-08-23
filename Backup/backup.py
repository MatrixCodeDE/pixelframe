import time
from pathlib import Path

from gevent.time import sleep as gsleep
from PIL import Image

from Canvas.canvas import Canvas
from Config.config import Config
from Misc.errors import IncorrectBackupSize
from Misc.utils import logger


class BackupHandler:
    config: Config
    canvas: Canvas
    path: Path
    running: bool

    def __init__(self, config: Config, canvas: Canvas) -> None:
        self.config = config
        self.canvas = canvas
        self.setup()
        self.restore_backup()
        self.running = True

    def setup(self):
        base = Path().resolve()
        self.path = base / self.config.backup.directory
        if not self.path.exists():
            self.path.mkdir()

    def create_backup(self):
        img: Image = self.canvas.get_canvas()
        img = img.convert("RGBA")
        name = time.strftime("backup_%Y_%m_%d_%H_%M_%S.png", time.gmtime())
        img.save(self.path / name)

    def restore_backup(self):
        latest: tuple[time.struct_time, Path | None] = (time.localtime(0), None)

        for entry in self.path.iterdir():
            if entry.is_file():
                t = time.strptime(entry.name, "backup_%Y_%m_%d_%H_%M_%S.png")
                if t > latest[0]:
                    latest = (t, entry)

        if latest[1] is not None:
            img = Image.open(latest[1]).convert("RGB")
            try:
                self.canvas.restore_from_image(img)
            except IncorrectBackupSize:
                raise IncorrectBackupSize(latest[1])

    def loop(self):
        logger.info(f"Starting Process: BACKUP.loop")

        while self.running:
            self.create_backup()
            gsleep(self.config.backup.interval)
