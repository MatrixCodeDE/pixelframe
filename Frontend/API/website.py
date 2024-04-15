from fastapi import APIRouter
from starlette.responses import HTMLResponse


class WebsiteAPI:

    router: APIRouter

    def __init__(self):
        self.router = APIRouter()
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_class=HTMLResponse)
        def get_website():
            with open("Frontend/API/webtemp.html", "r") as temp:
                web = temp.read()
            return web
