import logging
from typing import Callable, Any

from greenlet import GreenletExit

logger = logging.getLogger("pixelframe")


class EventHandler:
    events: dict[str, Callable]

    def __init__(self):
        self.events = {}

    def register(self, name: str) -> Any:
        """
        Registers a new event for the canvas
        Args:
            name (str): the name for fire the event

        Returns:
            The decorator
        """

        logger.info("Registered event: " + name)

        def decorator(func: Callable) -> Any:
            """
            The decorator for registering events
            Args:
                func (Callable): The function that should be fired

            Returns:
                The function
            """
            self.events[name] = func
            return func

        return decorator

    def trigger(self, name: str, *args, **kwargs) -> None:
        """
        Fires an existing event
        Args:
            name (str): The name of the event
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            None
        """
        if name in self.events:
            try:
                self.events[name](self, *args, **kwargs)
            except GreenletExit:
                raise
            except:
                logger.exception("Error in callback for %r", name)

    def exit(self):
        for event, call in self.events.items():
            if "exit" in event:
                call()
