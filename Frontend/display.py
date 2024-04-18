import time
from typing import Optional

import pygame
from gevent import Greenlet, spawn
from gevent.time import sleep as gsleep
from PIL.Image import Image
from pygame import Surface, SurfaceType

from Canvas.canvas import Canvas
from Config.config import Config
from Misc.Template.pixelmodule import PixelModule
from Misc.utils import event_handler, logger


class Display(PixelModule):
    config: Config
    canvas: Canvas
    screen: Surface | SurfaceType | None
    loop_routine: Greenlet
    show_stats: bool

    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.config = canvas.config
        self.show_stats = self.config.visuals.statsbar.enabled
        pygame.init()
        pygame.mixer.quit()
        pygame.display.set_caption("PixelFrame")
        pygame.font.init()
        self.screen = pygame.display.set_mode(self.config.visuals.size.get_size())
        super().__init__("CANVAS")

    def register_events(self):

        super().register_events()

        @event_handler.register("KEYDOWN-s")
        def on_keydown_s(*args, **kwargs):
            self.show_stats = not self.show_stats
            logger.info(
                f"{'Showing' if self.show_stats else 'Hiding'} stats on the screen"
            )

        @event_handler.register("DISPLAY-exit")
        def on_exit(*args, **kwargs):
            self.stop()

    def loop(self):
        logger.info(f"Starting Process: {self.prefix}.loop")
        updates = 1.0 / self.config.frontend.display.fps

        while self.running:
            start = time.time()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.type == pygame.QUIT:
                        event_handler.trigger("stop")
                        return
                    elif event.type == pygame.KEYDOWN:
                        event_handler.trigger("KEYDOWN-" + event.unicode)

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
        self.running = False
        pygame.mixer.quit()
        pygame.quit()
