from fastapi import FastAPI

from .database import engine
from . import models, routes

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Notes & Knowledge Management System",
)

# Include the API routes from the routes module
app.include_router(routes.router)
