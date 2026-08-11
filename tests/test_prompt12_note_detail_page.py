"""
Prompt 12 Verification Tests per PROMPT_CHAIN.md

Prompt 12 — Note Detail Page:
- Implement /notes/{note_id}.
- Retrieve the requested Note.
- Render Note information.
- Render associated author information.
- Use Jinja2 route generation for navigation where required.
- Return an appropriate browser-facing 404 when the Note does not exist.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_team_notes.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _create_user(session, username="testuser", email="test@example.com"):
    user = models.User(username=username, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_note(session, title="Test Note", content="Test content", author_id=1):
    note = models.Note(title=title, content=content, author_id=author_id)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


# =============================================================================
# Valid Note Renders
# =============================================================================
def test_valid_note_renders():
    """A valid Note renders on the detail page."""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(
        db,
        title="Prompt 12 Detail Note",
        content="This is the detail page content.",
        author_id=user.id,
    )
    note_id = note.id
    db.close()

    response = client.get(f"/notes/{note_id}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "Prompt 12 Detail Note" in response.text
    assert "This is the detail page content." in response.text


# =============================================================================
# Author Information Renders
# =============================================================================
def test_author_information_renders():
    """The associated author information is rendered on the detail page."""
    db = TestingSessionLocal()
    user = _create_user(db, username="bob", email="bob@example.com")
    note = _create_note(db, title="Authored Note", content="Author content", author_id=user.id)
    note_id = note.id
    db.close()

    response = client.get(f"/notes/{note_id}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert "bob" in response.text


# =============================================================================
# Missing Note Returns HTML 404
# =============================================================================
def test_missing_note_returns_html_404():
    """Missing Note returns an appropriate browser-facing HTML 404."""
    response = client.get("/notes/99999")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "404" in response.text
    assert "Note not found" in response.text


# =============================================================================
# Invalid Path Parameter Receives Appropriate Validation/Error Response
# =============================================================================
def test_invalid_path_parameter_gets_appropriate_response():
    """Invalid path parameter receives the appropriate validation/error response."""
    response = client.get("/notes/abc")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "422" in response.text
    assert "Invalid request" in response.text


# =============================================================================
# Jinja2 Route Generation for Navigation
# =============================================================================
def test_jinja2_route_generation_for_navigation():
    """Templates use Jinja2 url_for route generation for navigation."""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Nav Note", content="Nav content", author_id=user.id)
    note_id = note.id
    db.close()

    # Notes list page uses url_for to generate the detail link
    list_response = client.get("/notes")
    assert list_response.status_code == 200
    assert f'href="http://testserver/notes/{note_id}"' in list_response.text or \
           f'href="/notes/{note_id}"' in list_response.text

    # Note detail page uses url_for to generate the back link
    detail_response = client.get(f"/notes/{note_id}")
    assert detail_response.status_code == 200
    assert "href=" in detail_response.text
    assert "/notes" in detail_response.text