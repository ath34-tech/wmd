def test_mock_login_returns_dummy_bearer_token(client):
    response = client.post("/api/auth/mock-login")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] == "mock-token-wmd-mvp"
