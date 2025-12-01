from __future__ import annotations

from fastapi.testclient import TestClient

from src.app_backend.main import app

client = TestClient(app)


def test_websocket_get_and_update_room() -> None:
    room_id = "ws-test-room"

    with client.websocket_connect(f"/ws/rooms/{room_id}") as websocket:
        # 1) Update room via websocket
        websocket.send_json(
            {"action": "update", "code": "print('hi')", "language": "python"}
        )
        updated = websocket.receive_json()
        assert updated["room_id"] == room_id
        assert updated["code"] == "print('hi')"
        assert updated["language"] == "python"

        # 2) Get current room state via websocket
        websocket.send_json({"action": "get"})
        current = websocket.receive_json()
        assert current["room_id"] == room_id
        assert current["code"] == "print('hi')"
        assert current["language"] == "python"
