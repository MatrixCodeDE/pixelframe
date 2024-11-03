import argparse

import gevent.monkey

gevent.monkey.patch_all()
from gevent import spawn

from Canvas.canvas import Canvas
from Clients.manager import manager as umanager
from Config.config import Config
from Misc.utils import logger, status


def main():
    """
    The main function of PixelFrame
    """

    parser = argparse.ArgumentParser(usage="python3 [-c configfile] main.py")

    parser.add_argument(
        "-c",
        "--config",
        dest="configfile",
        default="Config/config.json",
        type=str,
        help="specify a config file",
    )

    parser.add_argument(
        "-d",
        "--debug",
        dest="debugging",
        action="store_true",
        help="Aktiviert den Debug-Modus.",
    )

    args = parser.parse_args()

    if args.debugging:
        logger.info(f"Starting in DEBUG Mode")

    config = Config(args.configfile, args.debugging)
    status.update("config", config)
    logger.info(f"Loaded config from {args.configfile}")

    manager = umanager
    manager.set_config(config)

    canvas = Canvas(config)
    main_loop = spawn(canvas.loop)
    heart_loop = spawn(canvas.heart_loop)
    coroutines = [main_loop, heart_loop]

    if config.frontend.display.enabled:
        from Frontend.display import Display

        status.update("display", True)
        display = Display(canvas)
        display_loop = spawn(display.loop)
        coroutines.append(display_loop)

    if config.frontend.sockets.enabled:
        from Frontend.sockets import Socketserver

        status.update("socketserver", True)
        server = Socketserver(canvas, config)
        server_loop = spawn(server.loop)
        coroutines.append(server_loop)

    if config.frontend.api.enabled:
        from Frontend.API.pixelapi import PixelAPI

        status.update("api", True)
        api = PixelAPI(canvas, config)
        api_loop = spawn(api.loop)
        coroutines.append(api_loop)

    if config.backup.enabled:
        from Backup.backup import BackupHandler

        backup = BackupHandler(config, canvas)
        backup_loop = spawn(backup.loop)
        coroutines.append(backup_loop)

    if config.timelapse.enabled:
        from Backup.timelapse import TimelapseHandler

        timelapse = TimelapseHandler(config, canvas)
        timelapse_loop = spawn(timelapse.loop)
        coroutines.append(timelapse_loop)

    logger.info("Starting Processes...")

    try:
        gevent.joinall(coroutines)
    except KeyboardInterrupt:
        logger.warn("Exitting...")
    canvas.stop()
    for coro in coroutines:
        coro.kill()


if __name__ == "__main__":
    main()
