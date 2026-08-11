"""
Slice 1 Verification Tests per VERIFICATION_PLAN.md

Tests S1-V01 through S1-V07 verify the Persistent User/Note Foundation + Create/View slice.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models

# Use a file-based SQLite database for testing to isolate from production data
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_team_notes.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the get_db dependency to use the test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the dependency override BEFORE creating tables
app.dependency_overrides[get_db] = override_get_db

# Create all tables in the test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean all tables before each test to ensure isolation."""
    # Drop and recreate all tables for clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _create_user(session, username="testuser", email="test@example.com"):
    """Helper to create a user directly in the database."""
    user = models.User(username=username, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_note(session, title="Test Note", content="Test content", author_id=1):
    """Helper to create a note directly in the database."""
    note = models.Note(title=title, content=content, author_id=author_id)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


# =============================================================================
# S1-V01 — Create Note Successfully
# =============================================================================
def test_s1_v01_create_note_successfully():
    """S1-V01: Create Note Successfully"""
    db = TestingSessionLocal()
    user = _create_user(db)
    db.close()

    response = client.post("/api/notes", json={
        "title": "My First Note",
        "content": "This is the content of my first note.",
        "author_id": user.id,
    })

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["title"] == "My First Note"
    assert data["content"] == "This is the content of my first note."
    assert data["author_id"] == user.id
    assert "id" in data


# =============================================================================
# S1-V02 — Persisted Note Can Be Retrieved
# =============================================================================
def test_s1_v02_persisted_note_can_be_retrieved():
    """S1-V02: Persisted Note Can Be Retrieved"""
    db = TestingSessionLocal()
    user = _create_user(db)
    user_id = user.id
    note = _create_note(db, title="Persisted Note", content="Persisted content", author_id=user_id)
    note_id = note.id
    db.close()

    response = client.get(f"/api/notes/{note_id}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Persisted Note"
    assert data["content"] == "Persisted content"
    assert data["author_id"] == user_id


# =============================================================================
# S1-V03 — Notes List Returns Persisted Notes
# =============================================================================
def test_s1_v03_notes_list_returns_persisted_notes():
    """S1-V03: Notes List Returns Persisted Notes"""
    db = TestingSessionLocal()
    user = _create_user(db)
    _create_note(db, title="Note 1", content="Content 1", author_id=user.id)
    _create_note(db, title="Note 2", content="Content 2", author_id=user.id)
    db.close()

    response = client.get("/api/notes")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    titles = {n["title"] for n in data}
    assert "Note 1" in titles
    assert "Note 2" in titles


# =============================================================================
# S1-V04 — Missing Note Returns 404
# =============================================================================
def test_s1_v04_missing_note_returns_404():
    """S1-V04: Missing Note Returns 404"""
    response = client.get("/api/notes/99999")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


# =============================================================================
# S1-V05 — Invalid Note Input Returns 422
# =============================================================================
def test_s1_v05_invalid_note_input_returns_422():
    """S1-V05: Invalid Note Input Returns 422"""
    response = client.post("/api/notes", json={
        "title": "",  # empty title should be invalid
        # missing content
        # missing author_id
    })

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

    # Verify no note was persisted
    db = TestingSessionLocal()
    count = db.query(models.Note).count()
    db.close()
    assert count == 0, f"Expected 0 notes but found {count}"


# =============================================================================
# S1-V06 — Missing User Returns 404
# =============================================================================
def test_s1_v06_missing_user_returns_404():
    """S1-V06: Missing User Returns 404"""
    response = client.post("/api/notes", json={
        "title": "Note for nobody",
        "content": "This user does not exist.",
        "author_id": 99999,
    })

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"

    # Verify no note was persisted
    db = TestingSessionLocal()
    count = db.query(models.Note).count()
    db.close()
    assert count == 0, f"Expected 0 notes but found {count}"


# =============================================================================
# S1-V07 — Database Persistence Survives Request Completion
# =============================================================================
def test_s1_v07_database_persistence_survives_request_completion():
    """S1-V07: Database Persistence Survives Request Completion"""
    db = TestingSessionLocal()
    user = _create_user(db)
    db.close()

    response = client.post("/api/notes", json={
        "title": "Persistence Test",
        "content": "This note must survive.",
        "author_id": user.id,
    })

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    created_note = response.json()
    note_id = created_note["id"]

    # Verify the note exists in the database after the request completed
    db = TestingSessionLocal()
    persisted_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    db.close()

    assert persisted_note is not None, "Note was not found in the database after creation"
    assert persisted_note.title == "Persistence Test"
    assert persisted_note.content == "This note must survive."
    assert persisted_note.author_id == user.id