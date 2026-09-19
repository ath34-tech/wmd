from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mock_login_returns_dummy_bearer_token():
    response = client.post("/api/auth/mock-login")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] == "mock-token-wmd-mvp"
