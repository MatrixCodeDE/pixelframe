import logging

from gevent import spawn

from canvas import Canvas
from sockets import Client, Server
from utils import logger

def register_events(canvas: Canvas) -> None:
    """
    Registers the needed events for the server
    Args:
        canvas (Canvas): The canvas object

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
        help += ">>> TEXT x y text (currently disabled)\n"
        help += ">>> PX x y [RRGGBB[AA]]\n"
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
            client.pps = 100000
            client.send("You are now god (%d pps)" % client.pps)
        else:
            client.pps = 100
            client.send("You are no longer god (%d pps)" % client.pps)

    logger.info("Successfully registered Events")


def main():
    """
    The main function of PixelFrame
    """
    canvas = Canvas((1920, 1080), (40, 30))

    register_events(canvas)

    logger.info("Starting Canvas Loop")
    main_loop = spawn(canvas.loop)
    main_loop.start()

    server = Server(canvas, "0.0.0.0", 1234)
    canvas.set_server(server)

    logger.info(f"Starting Server at {server.host}:{server.port}")
    server_loop = spawn(server.loop)

    try:
        server_loop.join()
    except KeyboardInterrupt:
        print("Exitting...")
    canvas.stop()
    server.stop()
    main_loop.kill()
    server_loop.kill()


if __name__ == "__main__":
    main()