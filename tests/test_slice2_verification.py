"""
Slice 2 Verification Tests per VERIFICATION_PLAN.md

Tests S2-V01 through S2-V10 verify Complete Note CRUD + Cascade behavior.
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
# S2-V01 — PUT Replaces Note Data
# Given: An existing Note.
# When: A valid complete update is submitted through PUT /api/notes/{note_id}.
# Then: The updated fields contain the new values. The response contains the updated Note.
# =============================================================================
def test_s2_v01_put_replaces_note_data():
    """S2-V01: PUT Replaces Note Data"""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Original Title", content="Original content", author_id=user.id)
    note_id = note.id
    db.close()

    response = client.put(f"/api/notes/{note_id}", json={
        "title": "Replaced Title",
        "content": "Replaced content",
    })

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["title"] == "Replaced Title"
    assert data["content"] == "Replaced content"
    assert data["id"] == note_id


# =============================================================================
# S2-V02 — PUT Missing Note Returns 404
# When: PUT targets a nonexistent note.
# Then: The API returns 404 Not Found.
# =============================================================================
def test_s2_v02_put_missing_note_returns_404():
    """S2-V02: PUT Missing Note Returns 404"""
    response = client.put("/api/notes/99999", json={
        "title": "Won't work",
        "content": "No note here",
    })

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


# =============================================================================
# S2-V03 — PATCH Updates Only Supplied Fields
# Given: A Note with a known title and body.
# When: PATCH submits only a new title.
# Then: The title changes. The body remains exactly unchanged.
# =============================================================================
def test_s2_v03_patch_updates_only_supplied_fields():
    """S2-V03: PATCH Updates Only Supplied Fields"""
    db = TestingSessionLocal()
    user = _create_user(db)
    original_body = "This is the original body content."
    note = _create_note(db, title="Original Title", content=original_body, author_id=user.id)
    note_id = note.id
    db.close()

    response = client.patch(f"/api/notes/{note_id}", json={
        "title": "Patched Title",
        # content is NOT supplied
    })

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["title"] == "Patched Title"
    assert data["content"] == original_body, (
        f"Content should remain '{original_body}', got '{data['content']}'"
    )


# =============================================================================
# S2-V04 — PATCH Missing Note Returns 404
# When: PATCH targets a nonexistent note.
# Then: The API returns 404 Not Found.
# =============================================================================
def test_s2_v04_patch_missing_note_returns_404():
    """S2-V04: PATCH Missing Note Returns 404"""
    response = client.patch("/api/notes/99999", json={
        "title": "Won't work",
    })

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


# =============================================================================
# S2-V05 — Invalid Update Data Returns 422
# When: Invalid PUT or PATCH data is submitted.
# Then: The request is rejected. The existing Note is not incorrectly modified.
# =============================================================================
def test_s2_v05_invalid_put_data_returns_422():
    """S2-V05: Invalid PUT Data Returns 422"""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Safe Note", content="Safe content", author_id=user.id)
    note_id = note.id
    db.close()

    response = client.put(f"/api/notes/{note_id}", json={
        # missing required 'title' field
        "content": "invalid update",
    })

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

    # Verify the note was NOT modified
    db2 = TestingSessionLocal()
    db_note = db2.query(models.Note).filter(models.Note.id == note_id).first()
    db2.close()
    assert db_note.title == "Safe Note"


# =============================================================================
# S2-V06 — DELETE Note Returns 204
# Given: An existing Note.
# When: DELETE /api/notes/{note_id} is requested.
# Then: The response status is 204 No Content. The response contains no body.
#       A subsequent lookup returns 404.
# =============================================================================
def test_s2_v06_delete_note_returns_204():
    """S2-V06: DELETE Note Returns 204"""
    db = TestingSessionLocal()
    user = _create_user(db)
    note = _create_note(db, title="Delete Me", content="Gone soon", author_id=user.id)
    note_id = note.id
    db.close()

    response = client.delete(f"/api/notes/{note_id}")

    assert response.status_code == 204, f"Expected 204, got {response.status_code}: {response.text}"
    assert response.content == b"" or response.text == "", "Expected empty response body"

    # Verify subsequent lookup returns 404
    lookup = client.get(f"/api/notes/{note_id}")
    assert lookup.status_code == 404, f"Expected 404 on subsequent lookup, got {lookup.status_code}"


# =============================================================================
# S2-V07 — DELETE Missing Note Returns 404
# When: DELETE targets a nonexistent note.
# Then: The API returns 404 Not Found.
# =============================================================================
def test_s2_v07_delete_missing_note_returns_404():
    """S2-V07: DELETE Missing Note Returns 404"""
    response = client.delete("/api/notes/99999")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


# =============================================================================
# S2-V08 — DELETE User Returns 204
# Given: An existing User.
# When: DELETE /api/users/{user_id} is requested.
# Then: The response status is 204 No Content.
# =============================================================================
def test_s2_v08_delete_user_returns_204():
    """S2-V08: DELETE User Returns 204"""
    db = TestingSessionLocal()
    user = _create_user(db)
    user_id = user.id
    db.close()

    response = client.delete(f"/api/users/{user_id}")

    assert response.status_code == 204, f"Expected 204, got {response.status_code}: {response.text}"


# =============================================================================
# S2-V09 — User Deletion Cascades to Notes
# Given: A User with multiple Notes.
# When: The User is deleted.
# Then: The User no longer exists. The User's Notes no longer exist.
#       No orphaned Notes remain for that User.
# =============================================================================
def test_s2_v09_user_deletion_cascades_to_notes():
    """S2-V09: User Deletion Cascades to Notes"""
    db = TestingSessionLocal()
    user = _create_user(db)
    user_id = user.id
    _create_note(db, title="Note A", content="Content A", author_id=user_id)
    _create_note(db, title="Note B", content="Content B", author_id=user_id)
    db.close()

    # Confirm notes exist before deletion
    db2 = TestingSessionLocal()
    notes_before = db2.query(models.Note).filter(models.Note.author_id == user_id).count()
    db2.close()
    assert notes_before == 2, f"Expected 2 notes before deletion, got {notes_before}"

    # Delete the user
    response = client.delete(f"/api/users/{user_id}")
    assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    # Confirm user no longer exists
    db3 = TestingSessionLocal()
    db_user = db3.query(models.User).filter(models.User.id == user_id).first()
    assert db_user is None, "User should no longer exist"

    # Confirm notes no longer exist (cascade)
    notes_after = db3.query(models.Note).filter(models.Note.author_id == user_id).count()
    db3.close()
    assert notes_after == 0, f"Expected 0 notes after cascade deletion, got {notes_after}"


# =============================================================================
# S2-V10 — DELETE Missing User Returns 404
# When: DELETE targets a nonexistent User.
# Then: The API returns 404 Not Found.
# =============================================================================
def test_s2_v10_delete_missing_user_returns_404():
    """S2-V10: DELETE Missing User Returns 404"""
    response = client.delete("/api/users/99999")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"