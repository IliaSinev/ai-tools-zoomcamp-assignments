from __future__ import annotations

import time
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["python", "javascript", "typescript", "sql", "java", "c", "cpp"]


SUPPORTED_LANGUAGES: Dict[str, Language] = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "sql": "sql",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
}


def normalize_language(lang: Optional[str]) -> Language:
    """Normalize an arbitrary language string to one of the supported languages."""
    if not lang:
        return "python"

    lower = lang.lower()
    if lower in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[lower]

    # Try to be forgiving with display-style names
    mapping = {
        "c++": "cpp",
        "js": "javascript",
        "ts": "typescript",
    }
    if lower in mapping:
        return SUPPORTED_LANGUAGES[mapping[lower]]

    return "python"


class RoomState(BaseModel):
    room_id: str = Field(..., description="Unique room identifier")
    code: str = Field("", description="Shared code in the room")
    language: Language = Field("python", description="Programming language")
    last_updated: float = Field(default_factory=time.time, description="Unix timestamp of last update")


class RoomCreateRequest(BaseModel):
    code: str = Field("", description="Optional initial code")
    language: Optional[str] = Field(None, description="Optional initial language")


class RoomCreateResponse(RoomState):
    pass


class RoomUpdateRequest(BaseModel):
    code: Optional[str] = Field(None, description="New code contents")
    language: Optional[str] = Field(None, description="New language")


class RoomListResponse(BaseModel):
    rooms: Dict[str, RoomState]
