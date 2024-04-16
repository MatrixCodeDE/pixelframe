import logging

logger = logging.getLogger("pixelframe")
logging.basicConfig(level=logging.INFO)


class NoFrontendException(Exception):
    def __init__(self):
        super().__init__("You cant disable all frontends!")


def confirm():
    inp = input("Do you want to continue? (Y/N) ")
    if inp.lower() == "y":
        return True
    else:
        exit(1)
