from fastapi import APIRouter
from starlette.responses import HTMLResponse


class WebserviceAPI:

    router: APIRouter
    template: str

    def __init__(self):
        self.router = APIRouter()
        with open("Misc/Template/webtemp.html", "r") as temp:
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
