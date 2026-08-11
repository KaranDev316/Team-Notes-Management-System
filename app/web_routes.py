from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import get_db

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


@router.get("/notes", response_class=HTMLResponse, include_in_schema=False)
def read_notes(request: Request, db: Session = Depends(get_db)):
    """
    Server-rendered page listing all notes.
    """
    notes = db.query(models.Note).all()
    return templates.TemplateResponse(
        request=request,
        name="notes_list.html",
        context={"notes": notes},
    )


@router.get("/notes/{note_id}", response_class=HTMLResponse, include_in_schema=False)
def read_note_detail(request: Request, note_id: int, db: Session = Depends(get_db)):
    """
    Server-rendered page showing a single note with its author information.
    """
    note = (
        db.query(models.Note)
        .filter(models.Note.id == note_id)
        .first()
    )
    if note is None:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "status_code": 404,
                "message": "Note not found",
            },
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="note_detail.html",
        context={"note": note},
    )