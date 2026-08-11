"""
Prompt 13 Verification Tests per PROMPT_CHAIN.md

Prompt 13 — Browser Error Handling and Plain CSS:
- Implement the approved HTML error handling.
- Ensure browser-facing failures render appropriate HTML.
- Add the required plain HTML/CSS styling.
- Do not add a CSS framework.
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
# Valid Notes Page
# =============================================================================
def test_valid_notes_page():
    """The notes list page renders successfully with HTML content."""
    db = TestingSessionLocal()
    user = _create_user(db)
    _create_note(db, title="P13 List Note", content="List content", author_id=user.id)
    db.close()

    response = client.get("/notes")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"].startswith("text/html")
    assert "P13 List Note" in response.text


# =============================================================================
# Valid Detail Page
# =============================================================================
def test_valid_detail_page():
    """The note detail page renders successfully with HTML content."""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="P13 Detail Note", content="Detail content", author_id=user.id)
    note_id = note.id
    db.close()

    response = client.get(f"/notes/{note_id}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"].startswith("text/html")
    assert "P13 Detail Note" in response.text
    assert "Detail content" in response.text


# =============================================================================
# Missing Note
# =============================================================================
def test_missing_note_renders_html_404():
    """A missing note produces an appropriate HTML 404 response."""
    response = client.get("/notes/99999")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert response.headers["content-type"].startswith("text/html")
    assert "404" in response.text
    assert "Note not found" in response.text


# =============================================================================
# Invalid Note ID
# =============================================================================
def test_invalid_note_id_renders_html_error():
    """An invalid note ID produces an appropriate HTML error response."""
    response = client.get("/notes/abc")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    assert response.headers["content-type"].startswith("text/html")
    assert "422" in response.text
    assert "Invalid request" in response.text


# =============================================================================
# Navigation
# =============================================================================
def test_navigation_between_list_and_detail():
    """Navigation between list and detail pages works."""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="P13 Nav Note", content="Nav content", author_id=user.id)
    note_id = note.id
    db.close()

    # List contains a link to the detail page
    list_response = client.get("/notes")
    assert list_response.status_code == 200
    assert f"/notes/{note_id}" in list_response.text

    # Detail page contains the back link to the list
    detail_response = client.get(f"/notes/{note_id}")
    assert detail_response.status_code == 200
    assert "/notes" in detail_response.text


# =============================================================================
# HTML Content Type and Status Codes
# =============================================================================
def test_html_content_type_and_status_codes():
    """All browser-facing pages return HTML with appropriate status codes."""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Status Note", content="Status content", author_id=user.id)
    note_id = note.id
    db.close()

    # Valid pages return 200 with HTML
    for url in ["/notes", f"/notes/{note_id}"]:
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    # Error pages return appropriate status codes with HTML
    missing_response = client.get("/notes/99999")
    assert missing_response.status_code == 404
    assert missing_response.headers["content-type"].startswith("text/html")

    invalid_response = client.get("/notes/abc")
    assert invalid_response.status_code == 422
    assert invalid_response.headers["content-type"].startswith("text/html")


# =============================================================================
# Plain CSS Styling (No Framework)
# =============================================================================
def test_plain_css_styling_present_and_no_framework():
    """The pages use plain CSS styling without a CSS framework."""
    db = TestingSessionLocal()
    user = _create_user(db)
    _create_note(db, title="CSS Note", content="CSS content", author_id=user.id)
    db.close()

    response = client.get("/notes")

    # Plain CSS stylesheet is linked
    assert "/static/styles.css" in response.text

    # No CSS framework classes/CDN references (Bootstrap, Tailwind, Foundation, etc.)
    assert "bootstrap" not in response.text.lower()
    assert "tailwind" not in response.text.lower()
    assert "cdn" not in response.text.lower()

    # The stylesheet is served successfully
    css_response = client.get("/static/styles.css")
    assert css_response.status_code == 200
    assert css_response.headers["content-type"].startswith("text/css")