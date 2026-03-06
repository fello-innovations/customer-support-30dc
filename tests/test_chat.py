"""Integration tests for the 30DLC chatbot API."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# Patch settings before app import
@pytest.fixture(scope="module")
def mock_settings():
    with patch("app.config.Settings") as MockSettings:
        instance = MagicMock()
        instance.openai_api_key = "sk-test"
        instance.chatbot_api_key = "test-key"
        instance.vector_store_id = "vs_test"
        instance.model = "gpt-4o-mini"
        instance.max_tokens = 1024
        instance.session_ttl_seconds = 3600
        instance.allowed_origins = "*"
        MockSettings.return_value = instance
        yield instance


@pytest.fixture(scope="module")
def client(mock_settings):
    import os
    os.environ["OPENAI_API_KEY"] = "sk-test"
    os.environ["CHATBOT_API_KEY"] = "test-key"
    os.environ["VECTOR_STORE_ID"] = "vs_test"

    from app.main import app
    from app.services.session_store import init_session_store
    init_session_store(ttl_seconds=3600)

    with TestClient(app) as c:
        yield c


def test_health_no_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model" in data


def test_chat_missing_auth(client):
    resp = client.post("/chat", json={"message": "Hello"})
    assert resp.status_code == 422  # missing header → validation error


def test_chat_wrong_auth(client):
    resp = client.post("/chat", json={"message": "Hello"}, headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_chat_success(client):
    mock_output_item = MagicMock()
    mock_output_item.type = "message"
    mock_content = MagicMock()
    mock_content.type = "output_text"
    mock_content.text = "The 30DLC is a 30-day learning challenge."
    mock_output_item.content = [mock_content]

    mock_response = MagicMock()
    mock_response.id = "resp_abc123"
    mock_response.output = [mock_output_item]

    with patch("app.services.openai_service.chat", new=AsyncMock(return_value=("The 30DLC is a 30-day learning challenge.", "resp_abc123"))):
        resp = client.post(
            "/chat",
            json={"message": "What is 30DLC?"},
            headers={"X-API-Key": "test-key"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["answer"] == "The 30DLC is a 30-day learning challenge."
    assert data["response_id"] == "resp_abc123"


def test_chat_with_session_id(client):
    with patch("app.services.openai_service.chat", new=AsyncMock(return_value=("Scoring info here.", "resp_xyz"))):
        resp = client.post(
            "/chat",
            json={"message": "How does scoring work?", "session_id": "my-session-123"},
            headers={"X-API-Key": "test-key"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "my-session-123"


def test_clear_session(client):
    # Seed the session store directly (bypasses mocked openai_service)
    from app.services.session_store import get_session_store
    get_session_store().set_previous_response_id("to-delete", "resp_seed")

    resp = client.delete("/sessions/to-delete", headers={"X-API-Key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["cleared"] is True


def test_clear_nonexistent_session(client):
    resp = client.delete("/sessions/does-not-exist", headers={"X-API-Key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["cleared"] is False
