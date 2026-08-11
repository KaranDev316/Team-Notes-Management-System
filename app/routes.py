from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

router = APIRouter()


@router.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # SQLAlchemy's cascade="all, delete-orphan" on the User.notes relationship
    # will handle the deletion of associated notes when the user is deleted.
    db.delete(db_user)
    db.commit()
    return


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


@router.delete("/api/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(db_note)
    db.commit()
    return


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


@router.put("/api/notes/{note_id}", response_model=schemas.Note)
def update_note(note_id: int, note: schemas.NoteBase, db: Session = Depends(get_db)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    # Update the model instance with the new data from the request
    db_note.title = note.title
    db_note.content = note.content

    db.commit()
    db.refresh(db_note)
    return db_note


@router.patch("/api/notes/{note_id}", response_model=schemas.Note)
def partial_update_note(
    note_id: int, note: schemas.NoteUpdate, db: Session = Depends(get_db)
):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    # Get the update data, excluding any fields that were not set in the request
    update_data = note.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)
    return db_note