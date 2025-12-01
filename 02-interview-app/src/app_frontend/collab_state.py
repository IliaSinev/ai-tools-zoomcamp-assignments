from __future__ import annotations

import html
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

Language = Literal["python", "javascript", "typescript", "sql", "java", "c", "cpp"]

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "SQL": "sql",
    "Java": "java",
    "C": "c",
    "C++": "cpp",
}


@dataclass
class RoomState:
    """State shared by all users connected to the same room."""
    code: str = ""
    language: Language = "python"
    last_updated: float = field(default_factory=time.time)


class RoomsStore:
    """In-memory store for collaborative rooms (server-side global)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rooms: Dict[str, RoomState] = {}

    def get_or_create(self, room_id: str) -> RoomState:
        with self._lock:
            if room_id not in self._rooms:
                self._rooms[room_id] = RoomState()
            return self._rooms[room_id]

    def update(
        self,
        room_id: str,
        *,
        code: Optional[str] = None,
        language: Optional[Language] = None,
    ) -> RoomState:
        with self._lock:
            room = self._rooms.setdefault(room_id, RoomState())
            if code is not None:
                room.code = code
            if language is not None:
                room.language = language
            room.last_updated = time.time()
            return room

    def list_rooms(self) -> List[str]:
        with self._lock:
            return list(self._rooms.keys())


# Single global store used by all Streamlit sessions
GLOBAL_ROOMS_STORE = RoomsStore()


def generate_room_id() -> str:
    """Generate a short, shareable room ID."""
    return uuid.uuid4().hex[:8]


def normalize_language(lang_key: str) -> Language:
    """
    Normalize a language key (e.g. 'Python', 'python') to a supported Language
    or fall back to 'python'.
    """
    if not lang_key:
        return "python"
    lower = lang_key.lower()
    # Try display names and internal ids
    for display, internal in SUPPORTED_LANGUAGES.items():
        if lower == display.lower() or lower == internal.lower():
            return internal  # type: ignore[return-value]
    return "python"


def build_js_execution_iframe(code: str) -> str:
    """
    Build a sandboxed <iframe> HTML that executes JavaScript code safely
    in the browser. The code runs in an isolated iframe with `sandbox="allow-scripts"`.
    Output (console.log and errors) is captured into a <pre> element.
    """
    # Use JSON to safely embed the user code as a JS string
    code_json = json.dumps(code)

    inner_html = f"""
<!doctype html>
<html>
  <body>
    <pre id="output" style="white-space: pre-wrap; font-family: monospace;"></pre>
    <script>
      const userCode = {code_json};
      const output = document.getElementById('output');

      function log(msg) {{
        output.textContent += msg + "\\n";
      }}

      (function() {{
        const originalLog = console.log;
        console.log = function(...args) {{
          log(args.join(" "));
          originalLog.apply(console, args);
        }};
        try {{
          // Execute user code in this sandboxed iframe context
          // eslint-disable-next-line no-eval
          eval(userCode);
        }} catch (err) {{
          log("Error: " + err.toString());
        }} finally {{
          console.log = originalLog;
        }}
      }})();
    </script>
  </body>
</html>
    """.strip()

    # srcdoc must be HTML-escaped
    escaped_inner = html.escape(inner_html, quote=True)

    iframe_html = f"""
<iframe
  sandbox="allow-scripts"
  style="width: 100%; height: 100%; border: none;"
  srcdoc="{escaped_inner}"
></iframe>
    """.strip()

    return iframe_html
