from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

router = APIRouter()


@router.post("/api/notes", response_model=schemas.Note, status_code=201)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    # Verify that the referenced User exists.
    db_user = db.query(models.User).filter(models.User.id == note.author_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_note = models.Note(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


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