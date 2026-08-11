from fastapi import FastAPI

from .database import engine
from . import models, routes, web_routes

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Notes & Knowledge Management System",
)

# Include the API and Web routes from their respective modules
app.include_router(routes.router)
app.include_router(web_routes.router)
