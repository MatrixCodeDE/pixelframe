from typing import Optional


class Stats:
    canvas: Optional["Canvas"]
    server: Optional["Socketserver"]

    pixelstats: dict[str, int]

    def __init__(self, canvas: Optional["Canvas"], server: Optional["Socketserver"]):
        self.canvas = canvas
        self.server = server
        self.pixelstats = {}
        self.canvas.set_stats(self)

    def add_pixel(self, x, y) -> None:
        index = f"{x}-{y}"
        self.pixelstats[index] = self.pixelstats.get(index, 0) + 1

    def get_pixelstats(self) -> list[tuple[str, int]]:
        s = sorted(self.pixelstats.items(), key=lambda x: x[1], reverse=True)
        return s

    def get_pixelcount(self) -> int:
        count = 0
        for p in self.pixelstats.values():
            count += p
        return count
