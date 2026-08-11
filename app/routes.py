from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

router = APIRouter()


@router.get("/api/notes", response_model=List[schemas.Note])
def read_notes(db: Session = Depends(get_db)):
    notes = db.query(models.Note).all()
    return notes


@router.get("/api/notes/{note_id}", response_model=schemas.Note)
def read_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note