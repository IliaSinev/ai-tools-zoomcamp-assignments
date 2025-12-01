from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

# Backend base URL; configurable via env var
BACKEND_URL = os.getenv("COLLAB_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")


def _url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return BACKEND_URL + path


def create_room(code: str = "", language: str = "python") -> Dict[str, Any]:
    """
    Create a new room via the backend. Returns the JSON room dict:
    {room_id, code, language, last_updated}
    """
    resp = requests.post(
        _url("/rooms"),
        json={"code": code, "language": language},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def get_room(room_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch room state. Returns None if the room does not exist (404).
    Raises for other HTTP errors.
    """
    resp = requests.get(_url(f"/rooms/{room_id}"), timeout=5)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def update_room(
    room_id: str,
    *,
    code: Optional[str] = None,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update code and/or language for the room.
    Returns updated room JSON.
    """
    payload: Dict[str, Any] = {}
    if code is not None:
        payload["code"] = code
    if language is not None:
        payload["language"] = language

    resp = requests.patch(
        _url(f"/rooms/{room_id}"),
        json=payload,
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()
