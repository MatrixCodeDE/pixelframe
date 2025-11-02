import time
from pathlib import Path

import numpy as np
from gevent.time import sleep as gsleep

from Canvas.canvas import Canvas
from Config.config import Config
from Misc.errors import IncorrectBackupSize
from Misc.Template.pixelmodule import PixelModule
from Misc.utils import logger


class BackupHandler(PixelModule):
    config: Config
    canvas: Canvas
    path: Path
    running: bool

    def __init__(self, config: Config, canvas: Canvas) -> None:
        self.config = config
        self.canvas = canvas
        self.setup()
        try:
            restored = self.restore_backup()
            if restored:
                logger.info("Successfully restored from backup")
        except FileNotFoundError:
            logger.warning("No backup found")
        except ValueError:
            logger.warning(
                "Failed to restore from backup: The file seams to be corrupt."
            )
        self.running = True
        super().__init__("Backup")

    def setup(self):
        base = Path().resolve()
        self.path = base / self.config.backup.directory
        if not self.path.exists():
            self.path.mkdir()

    def create_backup(self):
        data: np.ndarray = self.canvas.get_raw_data()
        name = time.strftime("backup_%Y_%m_%d_%H_%M_%S.npy", time.gmtime())
        np.save(self.path / name, data)

    def restore_backup(self):
        latest: tuple[time.struct_time, Path | None] = (time.localtime(0), None)

        for entry in self.path.iterdir():
            if entry.is_file():
                t = time.strptime(entry.name, "backup_%Y_%m_%d_%H_%M_%S.npy")
                if t > latest[0]:
                    latest = (t, entry)

        if latest[1] is not None:
            arr = np.load(latest[1])
            try:
                self.canvas.restore_from_array(arr)
            except IncorrectBackupSize:
                raise IncorrectBackupSize(latest[1])
        return True

    def stop(self):
        self.running = False

    def loop(self):
        logger.info(f"Starting Process: BACKUP.loop")

        while self.running:
            self.create_backup()
            gsleep(self.config.backup.interval)
