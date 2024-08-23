class Stats:
    """
    The Stats of the canvas
    Attributes:
        pixelstats (dict): A dictionary with the stats
    """

    pixelstats: dict[str, int]

    def __init__(self):
        self.pixelstats = {}

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


stats = Stats()
