from __future__ import annotations

import time

from src.app_backend.models import normalize_language
from src.app_backend.store import RoomsStore


def test_normalize_language_known() -> None:
    assert normalize_language("python") == "python"
    assert normalize_language("PyThOn") == "python"
    assert normalize_language("javascript") == "javascript"
    assert normalize_language("c++") == "cpp"
    assert normalize_language("js") == "javascript"


def test_normalize_language_unknown_defaults_to_python() -> None:
    assert normalize_language("klingon") == "python"
    assert normalize_language("") == "python"
    assert normalize_language(None) == "python"  # type: ignore[arg-type]


def test_create_room_assigns_id_and_defaults() -> None:
    store = RoomsStore()
    room = store.create_room()
    assert len(room.room_id) == 8
    int(room.room_id, 16)  # should not raise
    assert room.code == ""
    assert room.language == "python"


def test_create_room_with_custom_code_and_language() -> None:
    store = RoomsStore()
    room = store.create_room(code="print('hi')", language="javascript")
    assert room.code == "print('hi')"
    assert room.language == "javascript"


def test_get_room_and_update_room() -> None:
    store = RoomsStore()
    room = store.create_room(code="a", language="python")
    room_id = room.room_id

    fetched = store.get_room(room_id)
    assert fetched is not None
    assert fetched.code == "a"

    before_ts = fetched.last_updated
    time.sleep(0.01)
    updated = store.update_room(room_id, code="b", language="javascript")
    assert updated is not None
    assert updated.code == "b"
    assert updated.language == "javascript"
    assert updated.last_updated > before_ts


def test_update_room_nonexistent_returns_none() -> None:
    store = RoomsStore()
    updated = store.update_room("doesnotexist", code="x")
    assert updated is None


def test_upsert_room_creates_and_updates() -> None:
    store = RoomsStore()

    # Create via upsert
    created = store.upsert_room("customid", code="hi", language="python")
    assert created.room_id == "customid"
    assert created.code == "hi"

    before_ts = created.last_updated
    time.sleep(0.01)
    updated = store.upsert_room("customid", code="bye")
    assert updated.room_id == "customid"
    assert updated.code == "bye"
    assert updated.last_updated > before_ts


def test_list_rooms_includes_created_rooms() -> None:
    store = RoomsStore()
    r1 = store.create_room(code="1")
    r2 = store.create_room(code="2")

    rooms = store.list_rooms()
    assert r1.room_id in rooms
    assert r2.room_id in rooms
    assert rooms[r1.room_id].code == "1"
    assert rooms[r2.room_id].code == "2"
