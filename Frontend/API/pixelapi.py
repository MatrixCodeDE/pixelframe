import logging
import random
from typing import Annotated, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from Canvas.canvas import Canvas
from Config.config import Config
from Frontend.API.admin import AdminAPI
from Frontend.API.canvas import CanvasAPI
from Frontend.API.website import WebserviceAPI
from Misc.security import create_access_token
from Misc.Template.pixelmodule import PixelModule
from Misc.utils import logger

LOGIN_CODES = [
    200,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    208,
    226,
    300,
    301,
    302,
    303,
    304,
    305,
    306,
    307,
    308,
    400,
    401,
    402,
    403,
    404,
    405,
    406,
    407,
    408,
    409,
    410,
    411,
    412,
    413,
    414,
    415,
    416,
    417,
    418,
    421,
    422,
    423,
    424,
    425,
    426,
    428,
    429,
    431,
    451,
    500,
    501,
    502,
    503,
    504,
    505,
    506,
    507,
    508,
    510,
    511,
]


class PixelAPI(PixelModule):
    """
    The API to control the canvas
    Attributes:
        base_api (FastAPI): The base API
        web_api (WebserviceAPI): The API router for the web service
        canvas_api (CanvasAPI): The API router for the canvas functions
        canvas (Canvas): The canvas itself
        config (Config): The config for everything
    """

    base_api: FastAPI
    web_api: WebserviceAPI
    canvas_api: CanvasAPI
    admin_api: AdminAPI
    canvas: Canvas
    config: Config

    def __init__(self, canvas: Canvas, config: Config):
        self.config = config
        self.base_api = FastAPI(
            title=f"{self.config.general.name} API",
            description="API endpoint for putting pixels on the canvas",
            version="b0.1",
            docs_url=None,
            debug=self.config.debug,
        )
        self.canvas = canvas
        super().__init__("PixelAPI")
        self.register_routes()

        self.web_api = WebserviceAPI(self.base_api, self.config)
        self.base_api.include_router(self.web_api.router)

        self.canvas_api = CanvasAPI(self.base_api, self.canvas, self.config)
        self.base_api.include_router(self.canvas_api.router)

        self.admin_api = AdminAPI(self.base_api, self.canvas, self.config)
        self.base_api.include_router(self.admin_api.router)

    def register_routes(self):
        @self.base_api.exception_handler(404)
        def custom_not_found(*args, **kwargs):
            return RedirectResponse("/docs?not_found=true")

        @self.base_api.post("/login", status_code=status.HTTP_200_OK)
        async def login(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        ):
            if not (form_data.username == "admin" and form_data.password == "root123"):
                codes = LOGIN_CODES
                code = random.choice(codes)
                raise HTTPException(status_code=code)
            access_token = create_access_token(form_data.username)
            return {"access_token": access_token, "token_type": "bearer"}

    def loop(self):
        """
        The loop for the API
        """
        logger.info(f"Starting Process: {self.prefix}.loop")

        uvicorn.run(
            self.base_api,
            host=self.config.connection.host,
            port=self.config.connection.ports.api,
            # log_level=logging.WARN,
        )
