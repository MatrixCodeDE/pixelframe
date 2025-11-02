from typing import Any

from fastapi import HTTPException
from starlette import status


class NoConfigError(Exception):
    def __init__(self, config_file: str):
        super().__init__(f"No config file was found at the given path: {config_file}")


class MalformedConfigError(Exception):
    def __init__(self, filename: str | tuple[Any, ...], *additional: tuple[str]):
        if isinstance(filename, tuple):
            filename = ", ".join(str(filename))
        base = f"The provided Config file is malformed: {filename}"
        if additional:
            base += "\nAdditional information:"
            for a in additional:
                base += f"\n  {str(a)}"

        super().__init__(base)


class IncorrectBackupSize(Exception):
    def __init__(self, file: Any = None):
        super().__init__(
            f"Incorrect backup size" + f" for file {file}" if file is not None else ""
        )


class InvalidJSONFormat(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid json format",
        )


class InvalidColorFormat(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid color (hex) format",
        )


class SystemStop(Exception):
    def __init__(self):
        super().__init__("Stopping system")
