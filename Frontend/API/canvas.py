import time
from io import BytesIO

from fastapi import APIRouter, HTTPException
from PIL.Image import Image
from starlette.responses import StreamingResponse

from Canvas.canvas import Canvas
from Config.config import Config


class CanvasAPI:
    """
    The API router for all canvas endpoints
    Attributes:
        router (APIRouter): The router itself
        canvas (Canvas): The canvas
        config (Config): The config
    """
    router: APIRouter
    canvas: Canvas
    config: Config

    def __init__(self, canvas: Canvas, config: Config):
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
        def get_canvas():
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
        def get_size():
            """
            # Canvas size
            Returns the size of the canvas
            """
            size = self.canvas.get_size()
            return {"x": size[0], "y": size[1]}

        @self.router.get("/pixel")
        def get_pixel(x: int, y: int) -> str:
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

        @self.router.post("/pixel")
        def set_pixel(x: int, y: int, color: str):
            """
            # Set pixel color
            Sets the color of a given pixel
            """
            if not self.canvas.pixel_in_bounds(x, y):
                raise HTTPException(
                    status_code=422, detail="Pixel out of bounds. Try /canvas/size"
                )

            try:
                c = int(color, 16)
                if len(color) == 6:
                    r = (c & 0xFF0000) >> 16
                    g = (c & 0x00FF00) >> 8
                    b = c & 0x0000FF
                    a = 0xFF
                elif len(color) == 8:
                    r = (c & 0xFF000000) >> 24
                    g = (c & 0x00FF0000) >> 16
                    b = (c & 0x0000FF00) >> 8
                    a = c & 0x000000FF
                else:
                    raise HTTPException(
                        status_code=422, detail="Wrong color hex format."
                    )
            except ValueError:
                raise HTTPException(status_code=422, detail="Wrong color hex format.")
            self.canvas.add_pixel(x, y, r, g, b, a)

        @self.router.get("/since")
        def pixel_since(timestamp: int):
            """
            # Canvas changes since timestamp
            Returns all pixels changed since the given UNIX timestamp
            """
            out = self.canvas.get_pixel_since(timestamp)
            return out
