from __future__ import annotations

from fastapi.testclient import TestClient

from src.app_backend.main import app


client = TestClient(app)


def test_health_check() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_room_endpoint_with_defaults() -> None:
    resp = client.post("/rooms", json={})
    assert resp.status_code == 201
    data = resp.json()
    assert "room_id" in data
    assert len(data["room_id"]) == 8
    assert data["code"] == ""
    assert data["language"] == "python"
    assert isinstance(data["last_updated"], (float, int))


def test_create_room_endpoint_with_payload() -> None:
    payload = {"code": "console.log('hi')", "language": "javascript"}
    resp = client.post("/rooms", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == payload["code"]
    assert data["language"] == "javascript"


def test_get_room_and_404_for_missing() -> None:
    # Create one
    create_resp = client.post("/rooms", json={"code": "x"})
    room_id = create_resp.json()["room_id"]

    # Get it
    resp = client.get(f"/rooms/{room_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_id"] == room_id
    assert data["code"] == "x"

    # Non-existing
    resp_missing = client.get("/rooms/doesnotexist")
    assert resp_missing.status_code == 404
    assert "not found" in resp_missing.json()["detail"].lower()


def test_update_room_endpoint() -> None:
    # Create room
    create_resp = client.post("/rooms", json={"code": "a", "language": "python"})
    room_id = create_resp.json()["room_id"]

    # Update code and language
    payload = {"code": "b", "language": "javascript"}
    update_resp = client.patch(f"/rooms/{room_id}", json=payload)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["code"] == "b"
    assert data["language"] == "javascript"

    # Partial update (only code)
    payload2 = {"code": "c"}
    update_resp2 = client.patch(f"/rooms/{room_id}", json=payload2)
    assert update_resp2.status_code == 200
    data2 = update_resp2.json()
    assert data2["code"] == "c"
    assert data2["language"] == "javascript"  # unchanged


def test_update_nonexistent_room_returns_404() -> None:
    resp = client.patch("/rooms/doesnotexist", json={"code": "x"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_list_rooms_endpoint_contains_created_rooms() -> None:
    # Create two rooms
    r1 = client.post("/rooms", json={"code": "1"}).json()
    r2 = client.post("/rooms", json={"code": "2"}).json()

    resp = client.get("/rooms")
    assert resp.status_code == 200
    data = resp.json()
    assert "rooms" in data
    rooms = data["rooms"]
    assert r1["room_id"] in rooms
    assert r2["room_id"] in rooms
    assert rooms[r1["room_id"]]["code"] == "1"
    assert rooms[r2["room_id"]]["code"] == "2"
