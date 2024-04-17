from Misc.utils import event_handler


class PixelModule:
    prefix: str
    running: bool

    def __init__(self, name):
        self.name = name
        self.running = True
        self.register_events()

    def register_events(self):
        @event_handler.register(self.name + "-exit")
        def module_stop():
            self.stop()

    def stop(self):
        self.running = False
