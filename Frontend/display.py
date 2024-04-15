import time
from typing import Optional

import pygame
from gevent import Greenlet, spawn
from gevent.time import sleep as gsleep
from PIL.Image import Image
from pygame import Surface, SurfaceType

from Misc.utils import logger


class Display:
    config: Optional["Config"]
    canvas: Optional["Canvas"]
    socketserver: Optional["Socketserver"]

    screen: Surface | SurfaceType
    kill: bool
    loop_routine: Greenlet
    show_stats: bool

    def __init__(self, canvas: Optional["Canvas"]):
        self.canvas = canvas
        self.config = canvas.config
        self.kill = False
        self.show_stats = self.config.visuals.statsbar.enabled
        pygame.init()
        pygame.mixer.quit()
        pygame.display.set_caption("PixelFrame")
        pygame.font.init()
        self.screen = pygame.display.set_mode(self.config.visuals.size.get_size())

        self.register_events()

        self.loop_routine = spawn(self.loop)

    def set_socketserver(self, socketserver: Optional["Socketserver"]) -> None:
        self.socketserver = socketserver

    def register_events(self):

        logger.info("Registering events for 'DISPLAY'")

        @self.canvas.register("KEYDOWN-s")
        def on_keydown_s(*args, **kwargs):
            self.show_stats = not self.show_stats
            logger.info(
                f"{'Showing' if self.show_stats else 'Hiding'} stats on the screen"
            )

        logger.info("Successfully registered events for 'DISPLAY'")

    def loop(self):
        updates = 1.0 / 10

        while not self.kill:
            start = time.time()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.type == pygame.QUIT:
                        self.canvas.trigger("stop")
                        return
                    elif event.type == pygame.KEYDOWN:
                        self.canvas.trigger("KEYDOWN-" + event.unicode)

            self.render()

            end = time.time() - start
            gsleep(max(updates - end, 0))

    def render(self):

        image: Image = self.canvas.get_canvas()
        img = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        self.screen.fill((0, 0, 0))
        self.screen.blit(img, (0, 0))

        if self.show_stats:
            users: int = 0  # self.canvas.socketserver.user_count()
            pixel: int = self.canvas.stats.get_pixelcount()

            text: str = (
                f"Host: {self.config.connection.host} "
                f"| Socket: {self.config.connection.ports.socket} "
                f"| Users: {users} "
                f"| Pixels: {pixel}"
            )

            font = pygame.font.Font("Misc/font.otf", self.config.visuals.statsbar.size)
            outline = pygame.font.Font(
                "Misc/font_bold.otf", self.config.visuals.statsbar.size
            )
            rendertext = font.render(text, True, (255, 255, 255))
            renderoutline = outline.render(text, True, (0, 0, 0))

            tsx, tsy = font.size(text)
            self.screen.blit(
                renderoutline,
                (self.config.visuals.size.width / 2 - tsx / 2, tsy - tsy / 2),
            )
            self.screen.blit(
                rendertext,
                (self.config.visuals.size.width / 2 - tsx / 2, tsy - tsy / 2),
            )

        pygame.display.update()

    def stop(self):
        self.kill = True
        pygame.mixer.quit()
        pygame.quit()
