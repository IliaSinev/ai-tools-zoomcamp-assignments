from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status

from .models import (
    RoomCreateRequest,
    RoomCreateResponse,
    RoomListResponse,
    RoomState,
    RoomUpdateRequest,
)
from .store import RoomsStore

app = FastAPI(
    title="Collaborative Code App API",
    version="0.1.0",
    description="Backend API for collaborative code editor",
)

# Single in-process store instance
_rooms_store = RoomsStore()


def get_store() -> RoomsStore:
    return _rooms_store


@app.get("/health", summary="Health check")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post(
    "/rooms",
    response_model=RoomCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
)
async def create_room(
    payload: RoomCreateRequest,
    store: RoomsStore = Depends(get_store),
) -> RoomCreateResponse:
    room = store.create_room(
        code=payload.code,
        language=payload.language,
    )
    return RoomCreateResponse(**room.model_dump())


@app.get(
    "/rooms",
    response_model=RoomListResponse,
    summary="List all rooms",
)
async def list_rooms(
    store: RoomsStore = Depends(get_store),
) -> RoomListResponse:
    rooms = store.list_rooms()
    return RoomListResponse(rooms=rooms)


@app.get(
    "/rooms/{room_id}",
    response_model=RoomState,
    summary="Get room state",
)
async def get_room(
    room_id: str,
    store: RoomsStore = Depends(get_store),
) -> RoomState:
    room = store.get_room(room_id)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room '{room_id}' not found",
        )
    return room


@app.patch(
    "/rooms/{room_id}",
    response_model=RoomState,
    summary="Update existing room",
)
async def update_room(
    room_id: str,
    payload: RoomUpdateRequest,
    store: RoomsStore = Depends(get_store),
) -> RoomState:
    room = store.update_room(
        room_id,
        code=payload.code,
        language=payload.language,
    )
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room '{room_id}' not found",
        )
    return room

@app.websocket("/ws/rooms/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: str,
    store: RoomsStore = Depends(get_store),
) -> None:
    """
    Minimal WebSocket endpoint for room updates.

    Protocol (JSON messages):
      - {"action": "get"}:
          -> server responds with current room state
      - {"action": "update", "code": "...", "language": "..."}:
          -> server upserts state and broadcasts back updated room to this client

    For now we only echo back to the same client; in a more advanced impl you'd
    track connected sockets per room and broadcast to all of them.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "get":
                room = store.get_room(room_id)
                if room is None:
                    # If room does not exist yet, upsert it with defaults
                    room = store.upsert_room(room_id)
                await websocket.send_json(room.model_dump())

            elif action == "update":
                code = data.get("code")
                language = data.get("language")
                room = store.upsert_room(room_id, code=code, language=language)
                await websocket.send_json(room.model_dump())

            else:
                await websocket.send_json(
                    {"error": f"Unknown action: {action!r}"}
                )
    except WebSocketDisconnect:
        # Client disconnected; nothing special to do in this simple impl
        return
