from fastapi import APIRouter, FastAPI
from fastapi.params import Depends
from starlette import status

from Canvas.canvas import Canvas, Pixel
from Config.config import Config
from Frontend.API.models import PixelArray
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

        @self.router.put("/pixel", status_code=status.HTTP_201_CREATED)
        async def update_pixel(array: PixelArray):
            try:
                for ctp in array.pixels:
                    x, y, c = ctp
                    if not self.canvas.pixel_in_bounds(x, y):
                        print("error")
                        continue
                    r, g, b, a = hex_to_rgb(c, True)
                    pixel = Pixel(x, y, r, g, b, a)
                    self.canvas.put_pixel(pixel)

            except (TypeError, TypeError):
                raise InvalidJSONFormat()
