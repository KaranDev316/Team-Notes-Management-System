from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import engine
from . import models, routes, web_routes
from .web_routes import templates

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Notes & Knowledge Management System",
)

# Serve static files (CSS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the API and Web routes from their respective modules
app.include_router(routes.router)
app.include_router(web_routes.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Return an HTML error page for browser-facing HTTP errors
    (e.g. a missing note at /notes/99999) while preserving JSON
    responses for the API.
    """
    if request.url.path.startswith("/notes"):
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "status_code": exc.status_code,
                "message": exc.detail,
            },
            status_code=exc.status_code,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Return an HTML error page for browser-facing validation errors
    (e.g. /notes/abc) while preserving JSON 422 responses for the API.
    """
    if request.url.path.startswith("/notes"):
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "status_code": 422,
                "message": "Invalid request",
            },
            status_code=422,
        )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )