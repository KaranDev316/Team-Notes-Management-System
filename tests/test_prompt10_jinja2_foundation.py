from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_prompt10_simple_template_renders():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Jinja2 Foundation is working!" in response.text
    assert "<!DOCTYPE html>" in response.text
