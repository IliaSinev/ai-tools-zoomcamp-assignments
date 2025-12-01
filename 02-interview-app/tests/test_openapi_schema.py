from __future__ import annotations

from src.app_backend.main import app


def test_openapi_basic_structure() -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3."), "OpenAPI version should be 3.x"
    info = schema["info"]
    assert info["title"] == "Collaborative Code App API"
    assert info["version"] == "0.1.0"


def test_openapi_has_expected_paths() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    # Health endpoint
    assert "/health" in paths
    assert "get" in paths["/health"]

    # Rooms collection
    assert "/rooms" in paths
    rooms_path = paths["/rooms"]
    assert "get" in rooms_path
    assert "post" in rooms_path

    # Single room
    assert "/rooms/{room_id}" in paths
    single = paths["/rooms/{room_id}"]
    assert "get" in single
    assert "patch" in single


def test_openapi_room_create_response_schema_ref() -> None:
    schema = app.openapi()
    post_rooms = schema["paths"]["/rooms"]["post"]
    responses = post_rooms["responses"]

    # 201 response should use RoomCreateResponse schema
    assert "201" in responses
    resp_201 = responses["201"]
    content = resp_201["content"]["application/json"]["schema"]
    assert content["$ref"] == "#/components/schemas/RoomCreateResponse"


def test_openapi_components_include_room_schemas() -> None:
    schema = app.openapi()
    components = schema["components"]
    schemas = components["schemas"]

    # All our key models should be present
    expected = {
        "RoomState",
        "RoomCreateRequest",
        "RoomCreateResponse",
        "RoomUpdateRequest",
        "RoomListResponse",
    }

    for name in expected:
        assert name in schemas, f"Expected schema {name} in OpenAPI components"

    # Spot check fields for RoomState
    room_state = schemas["RoomState"]
    props = room_state["properties"]
    assert "room_id" in props
    assert props["room_id"]["type"] == "string"
    assert "code" in props
    assert props["code"]["type"] == "string"
    assert "language" in props
    assert "last_updated" in props
    assert props["last_updated"]["type"] in {"number", "integer"}
