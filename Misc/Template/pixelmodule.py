from Misc.eventhandler import event_handler


class PixelModule:
    """
    The base class for all modules
    Attributes:
        prefix (str): The prefix used for the events to identify the module
        running (bool): If the module is currently running
    """

    prefix: str
    running: bool

    def __init__(self, prefix: str):
        self.prefix = prefix.upper()
        self.running = True
        self.register_events()

    def register_events(self):
        """
        Registers all events for the class
        """

        @event_handler.register(self.prefix + "-exit")
        def module_stop(*args, **kwargs):
            self.stop()

    def stop(self):
        """
        Acts as a kind of 'killswitch' function
        Returns:
            None
        """
        self.running = False
