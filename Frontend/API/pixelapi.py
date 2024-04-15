from typing import Optional

import uvicorn
from fastapi import FastAPI

from Config.config import Config

from Frontend.API.website import WebsiteAPI

from Canvas.canvas import Canvas


class PixelAPI(FastAPI):

    canvas: Canvas
    config: Config

    def __init__(self, canvas: Canvas, config: Config):
        super().__init__(
            title=f"{config.general.name} API",
            description="API endpoint for putting pixels on the canvas",
            version="b0.1"
        )
        self.canvas = canvas
        self.config = config


def start_api(canvas: Canvas, config: Config):
    api = PixelAPI(canvas, config)
    webapi = WebsiteAPI()
    api.include_router(webapi.router)

    uvicorn.run(api, host=config.connection.host, port=config.connection.ports.api)