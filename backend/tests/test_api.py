def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rejects_unsupported_upload(client):
    response = client.post(
        "/api/documents",
        files={"file": ("notes.exe", b"hello", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_rejects_a_blank_question(client):
    response = client.post(
        "/api/conversations/00000000-0000-0000-0000-000000000001/messages",
        json={"content": "   "},
    )
    assert response.status_code == 422
