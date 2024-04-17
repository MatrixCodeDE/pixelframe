import argparse

import gevent.monkey

gevent.monkey.patch_all()
from gevent import spawn

from Canvas.canvas import Canvas
from Config.config import Config
from Frontend.sockets import Client
from Misc.utils import event_handler, logger
from Stats.stats import Stats


def register_events(canvas: Canvas, config: Config) -> None:
    """
    Registers the needed events for the server
    Args:
        canvas (Canvas): The canvas object
        config (Config): The config object

    Returns:
        None
    """

    logger.info("Registering events")

    @event_handler.register("stop")
    def stop(canvas: Canvas):
        canvas.stop()

    @event_handler.register("COMMAND-PX")
    def add_pixel(canvas: Canvas, client: Client, x, y, color=None):
        x, y = int(x), int(y)
        if color:
            c = int(color, 16)
            if len(color) == 6:
                r = (c & 0xFF0000) >> 16
                g = (c & 0x00FF00) >> 8
                b = c & 0x0000FF
                a = 0xFF
            elif len(color) == 8:
                r = (c & 0xFF000000) >> 24
                g = (c & 0x00FF0000) >> 16
                b = (c & 0x0000FF00) >> 8
                a = c & 0x000000FF
            else:
                return
            canvas.add_pixel(x, y, r, g, b, a)
            client.send("PX Success")
        else:
            r, g, b = canvas.get_pixel(x, y)
            client.send("PX %d %d %02x%02x%02x" % (x, y, r, g, b))

    @event_handler.register("COMMAND-HELP")
    def on_help(canvas: Canvas, client: Client):
        help = "Commands:\n"
        help += ">>> HELP\n"
        help += ">>> STATS\n"
        help += ">>> SIZE\n"
        help += ">>> QUIT\n"
        # help += ">>> TEXT x y text (currently disabled)\n"
        help += ">>> PX x y [RRGGBB[AA]]\n"
        help += f"Pixel per second per user: {client.pps}"
        client.send(help)

    @event_handler.register("COMMAND-STATS")
    def callback(canvas: Canvas, client: Client):
        d = canvas.get_pixel_color_count()
        import operator

        dSorted = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        dString = ""
        for k, v in dSorted:
            dString += str(k) + ":\t" + str(v) + "\n"
        client.send("Current pixel color distribution:\n" + dString)

    # @event_handler.register("COMMAND-TEXT")
    def on_text(canvas: Canvas, client: Client, x, y, *words):
        x, y = int(x), int(y)
        text = " ".join(words)[:200]
        canvas.text(x, y, text, delay=1)

    @event_handler.register("COMMAND-SIZE")
    def on_size(canvas: Canvas, client: Client):
        client.send("SIZE %d %d" % canvas.get_size())

    @event_handler.register("COMMAND-QUIT")
    def on_quit(canvas: Canvas, client: Client):
        client.disconnect()

    if config.game.godmode.enabled:

        @event_handler.register("COMMAND-GODMODE")
        def on_quit(canvas: Canvas, client: Client, mode):
            if mode == "on":
                client.set_pps(config.game.godmode.pps)
                client.send("You are now god (%d pps)" % client.pps)
            else:
                client.set_pps(config.game.pps)
                client.send("You are no longer god (%d pps)" % client.pps)

    logger.info("Successfully registered Events")


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

    register_events(canvas, config)

    logger.info("Starting Canvas Loop")

    if config.frontend.sockets.enabled:
        from Frontend.sockets import Socketserver

        server = Socketserver(canvas, config)
        server_loop = spawn(server.loop)
        coroutines.append(server_loop)

    if config.frontend.api.enabled:
        from Frontend.API.pixelapi import start_api

        api = spawn(start_api, canvas, config)
        coroutines.append(api)

    stats = Stats(canvas, server)

    try:
        gevent.joinall(coroutines)
    except KeyboardInterrupt:
        print("Exitting...")
    canvas.stop()
    for coro in coroutines:
        coro.kill()


if __name__ == "__main__":
    main()
