import json
from json import JSONDecodeError
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from Canvas.canvas import Canvas
from Config.config import Config
from Misc import security
from Misc.errors import InvalidJSONFormat
from Misc.utils import hex_to_rgb


class AdminAPI:
    """
    The API router for all canvas endpoints
    Attributes:
        router (APIRouter): The router itself
        canvas (Canvas): The canvas
        config (Config): The config
    """

    api: FastAPI
    router: APIRouter
    canvas: Canvas
    config: Config

    def __init__(self, api: FastAPI, canvas: Canvas, config: Config):
        self.api = api
        self.router = APIRouter(
            prefix="/admin",
            tags=["admin"],
            include_in_schema=True,
            dependencies=[Depends(security.get_admin)],
        )
        self.canvas = canvas
        self.config = config

        self.register_routes()

    def register_routes(self):
        @self.router.get("/reload")
        async def reload():
            self.config.reload()

        @self.router.put("/pixel")
        async def update_pixel(pixels: str):
            try:
                loaded = json.loads(pixels)

                if isinstance(loaded[0], list):  # list or colors
                    for ctp in loaded:
                        x, y, c = ctp
                        r, g, b, a = hex_to_rgb(c, True)
                        self.canvas.add_pixel(x, y, r, g, b, a)
                else:
                    x, y, c = loaded
                    r, g, b, a = hex_to_rgb(c, True)
                    self.canvas.add_pixel(x, y, r, g, b, a)

            except (JSONDecodeError, ValueError, TypeError):
                raise InvalidJSONFormat()
