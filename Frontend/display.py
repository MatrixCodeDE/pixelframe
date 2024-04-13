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

    screen: Surface | SurfaceType
    canvas: Surface | SurfaceType
    stats_screen: Surface | SurfaceType
    kill: bool
    loop_routine: Greenlet

    def __init__(self, canvas: Optional["Canvas"]):
        self.canvas = canvas
        self.config = canvas.config
        self.kill = False
        pygame.init()
        pygame.mixer.quit()
        pygame.display.set_caption("PixelFrame")
        pygame.font.init()
        self.screen = pygame.display.set_mode(self.config.visuals.size.get_size())
        self.stats_screen = Surface(
            self.config.visuals.size.get_size(), pygame.SRCALPHA
        )

        self.loop_routine = spawn(self.loop)

    def loop(self):
        updates = 1.0 / 5

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
        self.screen.blit(img, (0, 0))
        pygame.display.update()

    def stop(self):
        self.kill = True
        pygame.mixer.quit()
        pygame.quit()
