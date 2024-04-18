import argparse

import gevent.monkey

gevent.monkey.patch_all()
from gevent import spawn

from Canvas.canvas import Canvas
from Config.config import Config
from Frontend.sockets import Client
from Misc.utils import event_handler, logger
from Stats.stats import Stats


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

    args = parser.parse_args()

    config = Config(args.configfile)

    canvas = Canvas(config)
    main_loop = spawn(canvas.loop)
    heart_loop = spawn(canvas.heart_loop)
    coroutines = [main_loop, heart_loop]

    if config.frontend.display.enabled:
        from Frontend.display import Display

        display = Display(canvas)
        display_loop = spawn(display.loop)
        coroutines.append(display_loop)

    if config.frontend.sockets.enabled:
        from Frontend.sockets import Socketserver

        server = Socketserver(canvas, config)
        server_loop = spawn(server.loop)
        coroutines.append(server_loop)

    if config.frontend.api.enabled:
        from Frontend.API.pixelapi import PixelAPI

        api = PixelAPI(canvas, config)
        api_loop = spawn(api.loop)
        coroutines.append(api_loop)

    stats = Stats(canvas, server)

    logger.info("Starting Processes")

    try:
        gevent.joinall(coroutines)
    except KeyboardInterrupt:
        logger.warn("Exitting...")
    canvas.stop()
    for coro in coroutines:
        coro.kill()


if __name__ == "__main__":
    main()
