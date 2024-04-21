from fastapi import APIRouter, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse

from Config.config import Config
from Misc.utils import status


def custom_swagger_ui_html(title: str):
    html_content = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=title,
    )
    html_content_body = html_content.body.decode("utf-8")

    html_content_body = html_content_body.replace(
        "</body>",
        """
            <script type="text/javascript">
                var button = document.createElement("button");
                button.innerText = "Canvas";
                button.classList.add("main");
                button.style.position = "fixed";
                button.style.top = "50px";
                button.style.right = "20px";
                button.style.zIndex = "1000";
                button.style.fontFamily = "sans-serif";
                button.style.fontSize = "36px";
                button.style.fontWeight = "bold";
                button.style.color = "#3b4151";
                button.onclick = function() {
                    window.location.href = "/";
                };
                document.body.appendChild(button);
            </script>
        </body>""",
        1,
    )
    return HTMLResponse(content=html_content_body, status_code=html_content.status_code)


class WebserviceAPI:
    api: FastAPI
    config: Config
    router: APIRouter
    template: str

    def __init__(self, api: FastAPI, config: Config):
        self.api = api
        self.config = config
        self.router = APIRouter()
        with open("Misc/Template/Web/webtemp.html", "r") as temp:
            self.template = temp.read()
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_class=HTMLResponse)
        def get_webservice():
            """
            # Web Service
            Get the web service for displaying the canvas on your own device
            """
            return self.template

        @self.router.get("/docs", include_in_schema=False)
        def custom_swagger_ui():
            return custom_swagger_ui_html(self.api.title)

        @self.router.get("/status")
        def get_status():
            return status.get_status()
