import logging

logger = logging.getLogger("pixelframe")
logging.basicConfig(level=logging.DEBUG)


def confirm():
    inp = input("Do you want to continue? (Y/N) ")
    if inp.lower() == "y":
        return True
    else:
        exit(1)
