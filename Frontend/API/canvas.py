import time
from io import BytesIO

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from PIL import Image
from starlette import status

from Canvas.canvas import Canvas
from Clients.manager import manager
from Config.config import Config
from Misc.errors import InvalidColorFormat
from Misc.utils import cooldown_to_text, hex_to_rgb


class CanvasAPI:
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
        self.router = APIRouter(prefix="/canvas", tags=["canvas"])
        self.canvas = canvas
        self.config = config

        self.register_routes()

    def get_canvas_bytes(self, format: str, quality: int) -> BytesIO:
        """
        Returns the canvas as a BytesIO object
        Args:
            format (str): The format of the image
            quality (int): The quality of the image (1-100)
        Returns:
             A BytesIO object
        """
        pil_img: Image = self.canvas.get_canvas()
        pil_img = pil_img.convert("RGB")
        buf = BytesIO()
        pil_img.save(buf, format=format, quality=quality)
        buf.seek(0)
        return buf

    def register_routes(self):
        """
        Registers all endpoints for the router
        """

        @self.router.get(
            "/",
            responses={
                200: {"content": {"image/webp": {}}},
            },
            response_class=StreamingResponse,
        )
        async def get_canvas():
            """
            # Canvas Image
            Use this to get a webp image of the canvas
            """
            img = self.get_canvas_bytes("webp", 50)
            resp = StreamingResponse(content=img, media_type=f"image/webp")
            resp.headers["Cache-Control"] = "no-cache"
            resp.headers["Last-Modified"] = time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT", time.gmtime()
            )
            return resp

        @self.router.get("/size")
        async def get_size():
            """
            # Canvas size
            Returns the size of the canvas
            """
            size = self.canvas.get_size()
            return {"x": size[0], "y": size[1]}

        @self.router.get("/pps")
        async def get_pps(request: Request):
            """
            # User pps
            Returns the amount of pixels a user can place per second
            """
            return manager.client(request.client.host).get_pps()

        @self.router.get("/pixel")
        async def get_pixel(x: int, y: int) -> str:
            """
            # Pixel color
            Returns the color of a given pixel
            """
            pixel = self.canvas.get_pixel(x, y)
            if not pixel:
                raise HTTPException(
                    status_code=422, detail="Pixel out of bounds. Try /canvas/size"
                )
            return "%02x%02x%02x" % pixel

        @self.router.put("/pixel", status_code=status.HTTP_201_CREATED)
        async def set_pixel(x: int, y: int, color: str, request: Request):
            """
            # Set pixel color
            Sets the color of a given pixel
            """
            if not self.canvas.pixel_in_bounds(x, y):
                raise HTTPException(
                    status_code=422, detail="Pixel out of bounds. Try /canvas/size"
                )
            cd = manager.client(request.client.host).on_cooldown()
            # print(cd, manager.client(request.client.host))
            if cd != 0:
                raise HTTPException(
                    status_code=403, detail=f"On cooldown for {cooldown_to_text(cd)}"
                )

            try:
                r, g, b, a = hex_to_rgb(color, True)
            except ValueError:
                raise InvalidColorFormat()
            self.canvas.add_pixel(x, y, r, g, b, a)
            manager.client(request.client.host).update_cooldown()

        @self.router.get("/since", status_code=status.HTTP_200_OK)
        async def pixel_since(timestamp: int, response: Response, raw: bool = False):
            """
            # Canvas changes since timestamp
            Returns all pixels changed since the given UNIX timestamp. Use `raw` to get the changed pixels as a json object and avoid redirects on too many changed pixels.
            """
            redirect = RedirectResponse(url="/canvas/")
            if self.config.frontend.web.force_reload:
                return redirect
            out = self.canvas.get_pixel_since(timestamp)
            if len(out) > 1000 and not raw:
                return redirect
            response.status_code = status.HTTP_200_OK
            return out
