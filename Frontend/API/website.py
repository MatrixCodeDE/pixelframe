from fastapi import APIRouter, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from Config.config import Config
from Misc.utils import status


def custom_swagger_ui_html(title, favicon):
    """
    Returns a custom swagger ui with the navigation bar
    """
    html_content = get_swagger_ui_html(
        openapi_url="/openapi.json", title=title, swagger_favicon_url=favicon
    )
    html_content_body = html_content.body.decode("utf-8")
    html_content_body = html_content_body.replace(
        "</head>",
        """
        <link rel="stylesheet" href="static/navbar.css">
        </head>
        """,
        1,
    )
    html_content_body = html_content_body.replace(
        "<body>",
        """
        <body>
            <div class="navigation">
                <div class="title">
                    <img class="title-logo" src="static/icon.png" alt="Logo by Matrix">
                    <a class="title-text">PixelFrame</a>
                </div>
                <ul class="navbar">
                    <li class="nav-box nav-first">
                        <a class="nav-item" href="/">Canvas</a>
                    </li>
                    <li class="nav-box">
                        <a class="nav-item nav-active" href="/docs">API</a>
                    </li>
                    <li class="nav-box">
                        <a class="nav-item" href="/status">Status</a>
                    </li>
                    <li class="nav-box">
                        <a class="nav-item" href="https://github.com/MatrixCodeDE/pixelframe/blob/main/GUIDE.md">Guide</a>
                    </li>
                    <li class="nav-box nav-last">
                        <a class="nav-item" href="https://github.com/MatrixCodeDE/pixelframe">GitHub</a>
                    </li>
                </ul>
            </div>
            <div class="spacer"></div>
        """,
        1,
    )
    return HTMLResponse(content=html_content_body, status_code=html_content.status_code)


class WebserviceAPI:
    """
    The endpoint for all web stuff
    Attributes:
        api (FastAPI): The base API
        config (Config): The configuration
        router (APIRouter): The router (sub endpoint) of the API for the web stuff
    """
    api: FastAPI
    config: Config
    router: APIRouter

    def __init__(self, api: FastAPI, config: Config):
        self.api = api
        self.config = config
        self.router = APIRouter()
        self.api.mount("/web", StaticFiles(directory="Misc/Template/Web/"), name="web")
        self.api.mount(
            "/static", StaticFiles(directory="Misc/Template/Web/static"), name="static"
        )
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_class=HTMLResponse)
        def get_webservice():
            """
            # Web Service
            Get the web service for displaying the canvas on your own device
            """
            return RedirectResponse("/web/index.html", status_code=301)

        @self.router.get("/docs", include_in_schema=False)
        def custom_swagger_ui():
            return custom_swagger_ui_html(self.api.title, "/static/favicon.ico")

        @self.router.get("/status")
        def get_status():
            return status.get_status()
