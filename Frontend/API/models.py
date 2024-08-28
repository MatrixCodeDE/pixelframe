from pydantic import BaseModel


class PixelArray(BaseModel):
    pixels: list[tuple[int, int, str]] = [(0, 1, "ffffffff")]
