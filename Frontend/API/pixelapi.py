import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI

from Canvas.canvas import Canvas
from Config.config import Config
from Frontend.API.canvas import CanvasAPI
from Frontend.API.website import WebsiteAPI


class PixelAPI(FastAPI):

    canvas: Canvas
    config: Config

    def __init__(self, canvas: Canvas, config: Config):
        super().__init__(
            title=f"{config.general.name} API",
            description="API endpoint for putting pixels on the canvas",
            version="b0.1",
        )
        self.canvas = canvas
        self.config = config


def start_api(canvas: Canvas, config: Config):
    api = PixelAPI(canvas, config)

    webapi = WebsiteAPI()
    api.include_router(webapi.router)

    canvasapi = CanvasAPI(canvas, config)
    api.include_router(canvasapi.router)

    uvicorn.run(api, host=config.connection.host, port=config.connection.ports.api, log_level=logging.WARN)
