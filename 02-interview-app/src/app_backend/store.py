from __future__ import annotations

import threading
import time
import uuid
from typing import Dict, Optional

from .models import RoomState, normalize_language


class RoomsStore:
    """
    Thread-safe in-memory storage for room states.

    In real deployments you’d replace this with Redis / DB.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rooms: Dict[str, RoomState] = {}

    def generate_room_id(self) -> str:
        return uuid.uuid4().hex[:8]

    def create_room(self, *, code: str = "", language: Optional[str] = None) -> RoomState:
        room_id = self.generate_room_id()
        normalized_lang = normalize_language(language)
        ts = time.time()
        room = RoomState(
            room_id=room_id,
            code=code,
            language=normalized_lang,
            last_updated=ts,
        )
        with self._lock:
            self._rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[RoomState]:
        with self._lock:
            return self._rooms.get(room_id)

    def upsert_room(
        self,
        room_id: str,
        *,
        code: Optional[str] = None,
        language: Optional[str] = None,
    ) -> RoomState:
        with self._lock:
            existing = self._rooms.get(room_id)
            if existing is None:
                # Create a new room with defaults
                existing = RoomState(
                    room_id=room_id,
                    code=code or "",
                    language=normalize_language(language),
                    last_updated=time.time(),
                )
                self._rooms[room_id] = existing
                return existing

            data = existing.model_copy()
            if code is not None:
                data.code = code
            if language is not None:
                data.language = normalize_language(language)
            data.last_updated = time.time()
            self._rooms[room_id] = data
            return data

    def update_room(
        self,
        room_id: str,
        *,
        code: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Optional[RoomState]:
        with self._lock:
            existing = self._rooms.get(room_id)
            if existing is None:
                return None
            data = existing.model_copy()
            if code is not None:
                data.code = code
            if language is not None:
                data.language = normalize_language(language)
            data.last_updated = time.time()
            self._rooms[room_id] = data
            return data

    def list_rooms(self) -> Dict[str, RoomState]:
        with self._lock:
            # Return a shallow copy to avoid external mutation
            return dict(self._rooms)
