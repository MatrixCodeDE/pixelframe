import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI

from Canvas.canvas import Canvas
from Config.config import Config
from Frontend.API.canvas import CanvasAPI
from Frontend.API.website import WebserviceAPI
from Misc.Template.pixelmodule import PixelModule
from Misc.utils import logger


class PixelAPI(PixelModule):
    """
    The API to control the canvas
    Attributes:
        base_api (FastAPI): The base API
        web_api (WebserviceAPI): The API router for the web service
        canvas_api (CanvasAPI): The API router for the canvas functions
        canvas (Canvas): The canvas itself
        config (Config): The config for everything
    """

    base_api: FastAPI
    web_api: WebserviceAPI
    canvas_api: CanvasAPI
    canvas: Canvas
    config: Config

    def __init__(self, canvas: Canvas, config: Config):
        self.config = config
        self.base_api = FastAPI(
            title=f"{self.config.general.name} API",
            description="API endpoint for putting pixels on the canvas",
            version="b0.1",
        )
        self.canvas = canvas
        super().__init__("PixelAPI")

        self.web_api = WebserviceAPI()
        self.base_api.include_router(self.web_api.router)

        self.canvas_api = CanvasAPI(self.canvas, self.config)
        self.base_api.include_router(self.canvas_api.router)

    def loop(self):
        """
        The loop for the API
        """
        logger.info(f"Starting Process: {self.prefix}.fastAPI")

        uvicorn.run(
            self.base_api,
            host=self.config.connection.host,
            port=self.config.connection.ports.api,
            log_level=logging.WARN,
        )
