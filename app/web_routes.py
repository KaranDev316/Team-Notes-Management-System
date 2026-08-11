from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")
# Disable Jinja2 template cache to work around Python 3.14 / weakref compatibility issue
templates.env.cache = None


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    """
    A simple test route to verify that Jinja2 templates are being rendered.
    """
    return templates.TemplateResponse(request=request, name="index.html")
