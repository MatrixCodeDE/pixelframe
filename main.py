import logging

from gevent import spawn

from canvas import Canvas
from sockets import Client, Server
from stats import Stats
from utils import logger


def register_events(canvas: Canvas, cpps: int | float) -> None:
    """
    Registers the needed events for the server
    Args:
        canvas (Canvas): The canvas object
        cpps (int | float): Refers to default pps of the clients

    Returns:
        None
    """

    logger.info("Registering events")

    @canvas.register("render")
    def render(canvas: Canvas):
        canvas.render()

    @canvas.register("stop")
    def stop(canvas: Canvas):
        canvas.stop()

    @canvas.register("COMMAND-PX")
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
        else:
            r, g, b, a = canvas.get_pixel(x, y)
            client.send("PX %d %d %02x%02x%02x%02x" % (x, y, r, g, b, a))

    @canvas.register("COMMAND-HELP")
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

    @canvas.register("COMMAND-STATS")
    def callback(canvas: Canvas, client: Client):
        d = canvas.get_pixel_color_count()
        import operator
        dSorted = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        dString = ""
        for k, v in dSorted:
            dString += str(k) + ":\t" + str(v) + "\n"
        client.send("Current pixel color distribution:\n" + dString)

    # @canvas.register("COMMAND-TEXT")
    def on_text(canvas: Canvas, client: Client, x, y, *words):
        x, y = int(x), int(y)
        text = " ".join(words)[:200]
        canvas.text(x, y, text, delay=1)

    @canvas.register("COMMAND-SIZE")
    def on_size(canvas: Canvas, client: Client):
        client.send("SIZE %d %d" % canvas.get_size())

    @canvas.register("COMMAND-QUIT")
    def on_quit(canvas: Canvas, client: Client):
        client.disconnect()

    # @canvas.register("COMMAND-GODMODE")
    def on_quit(canvas: Canvas, client: Client, mode):
        if mode == "on":
            client.set_pps(100000)
            client.send("You are now god (%d pps)" % client.pps)
        else:
            client.set_pps(cpps)
            client.send("You are no longer god (%d pps)" % client.pps)

    logger.info("Successfully registered Events")


def main():
    """
    The main function of PixelFrame
    """

    import argparse, optparse

    parser = argparse.ArgumentParser(usage="python3 [options] main.py")

    parser.add_argument("-H", "--host", dest="hostname",
                        default="0.0.0.0", type=str,
                        help="specify hostname to run on")
    parser.add_argument("-P", "--port", dest="portnum", default=1234,
                        type=int, help="port number to run on")
    parser.add_argument("-pps", "--pips", dest="pixelpersecond", default=30,
                        type=int, help="amount of pixels a client can change per seconds")
    parser.add_argument("-sx", "--sizex", dest="sizex", default=1920,
                        type=int, help="canvas size x in pixels")
    parser.add_argument("-sy", "--sizey", dest="sizey", default=1080,
                        type=int, help="canvas size y in pixels")

    args = parser.parse_args()

    canvas = Canvas((args.sizex, args.sizey), (40, 30))

    register_events(canvas, args.pixelpersecond)

    logger.info("Starting Canvas Loop")
    main_loop = spawn(canvas.loop)

    server = Server(canvas, args.hostname, args.portnum, args.pixelpersecond)

    logger.info(f"Starting Server at {server.host}:{server.port}")
    server_loop = spawn(server.loop)

    stats = Stats(canvas, server)

    try:
        main_loop.start()
        server_loop.join()
    except KeyboardInterrupt:
        print("Exitting...")
    canvas.stop()
    server.stop()
    main_loop.kill()
    server_loop.kill()


if __name__ == "__main__":
    main()
