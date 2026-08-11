"""
Prompt 11 Verification Tests per VERIFICATION_PLAN.md

Tests S3-V01 through S3-V06 verify the Jinja2 Web Interface + Browser Errors slice.
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
# S3-V01 — Notes List Page Renders
# Given: Persisted Notes.
# When: The browser requests /notes.
# Then: The response succeeds. The response is HTML. The page contains the expected Notes.
# =============================================================================
def test_s3_v01_notes_list_page_renders():
    db = TestingSessionLocal()
    user = _create_user(db)
    _create_note(db, title="Visible Note A", content="Content A", author_id=user.id)
    _create_note(db, title="Visible Note B", content="Content B", author_id=user.id)
    db.close()

    response = client.get("/notes")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "Visible Note A" in response.text
    assert "Visible Note B" in response.text
    assert "<!DOCTYPE html>" in response.text


# =============================================================================
# S3-V02 — Note Detail Page Renders
# Given: An existing Note and User.
# When: The browser requests /notes/{note_id}.
# Then: The response succeeds. The response is HTML. The page displays the Note
#       information. The associated author information is displayed.
# =============================================================================
def test_s3_v02_note_detail_page_renders():
    db = TestingSessionLocal()
    user = _create_user(db, username="alice", email="alice@example.com")
    note = _create_note(
        db,
        title="Detail Test Note",
        content="This is the detail content.",
        author_id=user.id,
    )
    note_id = note.id
    db.close()

    response = client.get(f"/notes/{note_id}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "Detail Test Note" in response.text
    assert "This is the detail content." in response.text
    assert "alice" in response.text


# =============================================================================
# S3-V03 — Missing Note Produces HTML 404
# When: The browser requests /notes/{missing_note_id}.
# Then: The response status is 404. The response is an HTML response.
#       The page presents an appropriate error message.
# =============================================================================
def test_s3_v03_missing_note_produces_html_404():
    response = client.get("/notes/99999")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "404" in response.text
    assert "Note not found" in response.text


# =============================================================================
# S3-V04 — Invalid Path Parameter Produces Browser Error
# When: The browser requests a note URL with an invalid note ID format.
# Then: The request does not reach invalid database lookup logic.
#       The browser receives the appropriate validation/error response.
# =============================================================================
def test_s3_v04_invalid_path_parameter_produces_browser_error():
    response = client.get("/notes/abc")

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    assert response.headers["content-type"].startswith("text/html")
    assert "422" in response.text
    assert "Invalid request" in response.text


# =============================================================================
# S3-V05 — Navigation Works
# Given: The notes list contains Notes.
# When: A user follows a Note link.
# Then: The corresponding note detail page opens successfully.
# =============================================================================
def test_s3_v05_navigation_works():
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Navigation Note", content="Nav content", author_id=user.id)
    note_id = note.id
    db.close()

    # The notes list page must contain a link to the note detail page
    list_response = client.get("/notes")
    assert list_response.status_code == 200
    assert f'/notes/{note_id}' in list_response.text

    # Following the link opens the detail page successfully
    detail_response = client.get(f"/notes/{note_id}")
    assert detail_response.status_code == 200
    assert "Navigation Note" in detail_response.text


# =============================================================================
# S3-V06 — Template Context Is Sufficient
# When: The list and detail templates render.
# Then: Required template values are available. No additional data is required
#       from an undeclared source.
# =============================================================================
def test_s3_v06_template_context_is_sufficient():
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Context Note", content="Context content", author_id=user.id)
    note_id = note.id
    db.close()

    # Rendering both templates must succeed with the provided context
    list_response = client.get("/notes")
    assert list_response.status_code == 200
    assert "Context Note" in list_response.text

    detail_response = client.get(f"/notes/{note_id}")
    assert detail_response.status_code == 200
    assert "Context Note" in detail_response.text
    assert "Context content" in detail_response.text

    # Verify the static stylesheet is referenced so pages have plain CSS styling
    assert "/static/styles.css" in list_response.text
    assert "/static/styles.css" in detail_response.text