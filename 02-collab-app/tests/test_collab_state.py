from __future__ import annotations

import html
import time

from src.app_frontend.collab_state import (
    GLOBAL_ROOMS_STORE,
    RoomState,
    build_js_execution_iframe,
    generate_room_id,
    normalize_language,
)


def test_generate_room_id_has_expected_length_and_hex_chars() -> None:
    room_id = generate_room_id()
    assert len(room_id) == 8
    int(room_id, 16)  # should not raise


def test_normalize_language_known_display_name() -> None:
    assert normalize_language("Python") == "python"
    assert normalize_language("python") == "python"
    assert normalize_language("JavaScript") == "javascript"
    assert normalize_language("javascript") == "javascript"


def test_normalize_language_unknown_falls_back_to_python() -> None:
    assert normalize_language("Klingon") == "python"
    assert normalize_language("") == "python"
    assert normalize_language(" ") == "python"


def test_rooms_store_get_or_create_and_update() -> None:
    store = GLOBAL_ROOMS_STORE  # use the global store for simplicity

    room_id = generate_room_id()
    room = store.get_or_create(room_id)
    assert isinstance(room, RoomState)
    assert room.code == ""
    assert room.language == "python"

    # Update code and language
    before = room.last_updated
    time.sleep(0.01)
    updated = store.update(room_id, code="print('hello')", language="python")
    assert updated.code == "print('hello')"
    assert updated.language == "python"
    assert updated.last_updated > before

    # get_or_create again returns the same updated state
    again = store.get_or_create(room_id)
    assert again.code == "print('hello')"
    assert again.language == "python"


def test_build_js_execution_iframe_contains_sandbox_and_escaped_code() -> None:
    user_code = "console.log('hello <world>');"
    iframe_html = build_js_execution_iframe(user_code)

    # Contains sandboxed iframe
    assert "<iframe" in iframe_html
    assert 'sandbox="allow-scripts"' in iframe_html

    # The inner HTML is escaped inside srcdoc
    escaped_snippet = html.escape("console.log('hello <world>');", quote=True)
    assert escaped_snippet in iframe_html
