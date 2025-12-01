from __future__ import annotations

import time
from typing import Any, Dict, Tuple

import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_ace import st_ace

from api_client import create_room, get_room, update_room, BACKEND_URL
from collab_state import (
    SUPPORTED_LANGUAGES,
    build_js_execution_iframe,
    normalize_language,
)


def _extract_room_id(raw: Any) -> str | None:
    """
    Helper to normalize room id coming from st.query_params,
    which may be a string or a list of strings depending on Streamlit version.
    """
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw[0] if raw else None
    if isinstance(raw, str):
        return raw
    return str(raw)


def get_or_create_room_id_via_backend() -> str:
    """
    Get the room id from query params.
    If missing or pointing to a non-existent room, create a new room via backend
    and update the URL.
    """
    params = st.query_params
    room_param = _extract_room_id(params.get("room"))

    if room_param:
        # Check if room actually exists
        try:
            room = get_room(room_param)
        except requests.RequestException as exc:
            st.error(f"Failed to contact backend when checking room: {exc}")
            return room_param

        if room is not None:
            return room_param

        # Room ID is present but backend doesn't know it -> fall through and create new

    # No room param or room not found in backend -> create new
    try:
        new_room = create_room()
    except requests.RequestException as exc:
        st.error(f"Failed to create room via backend: {exc}")
        # Fallback: synthetic ID, but won't exist in backend
        return "fallback-room"

    new_room_id = new_room["room_id"]
    params["room"] = new_room_id  # updates URL
    return new_room_id


def sync_room_into_session(room_id: str) -> Tuple[Dict[str, Any], str]:
    """
    Synchronize backend room state with the current session_state.

    Returns (room_json, current_code_in_editor).
    """
    try:
        room = get_room(room_id)
    except requests.RequestException as exc:
        st.error(f"Failed to fetch room from backend: {exc}")
        # Minimal fallback room
        room = {
            "room_id": room_id,
            "code": st.session_state.get("code_editor", ""),
            "language": "python",
            "last_updated": st.session_state.get("code_version", time.time()),
        }

    if room is None:
        # If room disappeared, create a new one
        try:
            room = create_room()
        except requests.RequestException as exc:
            st.error(f"Failed to recreate room via backend: {exc}")
            room = {
                "room_id": room_id,
                "code": "",
                "language": "python",
                "last_updated": time.time(),
            }

    # Initialize local session state if first time
    if "code_editor" not in st.session_state:
        st.session_state["code_editor"] = room["code"]
        st.session_state["code_version"] = room["last_updated"]
        st.session_state["last_change_origin"] = "remote"

    # Remote update detection
    if room["last_updated"] > st.session_state.get("code_version", 0.0):
        if st.session_state.get("last_change_origin") != "local":
            st.session_state["code_editor"] = room["code"]
            st.session_state["code_version"] = room["last_updated"]
        st.session_state["last_change_origin"] = "remote"

    current_code = st.session_state["code_editor"]
    return room, current_code

def check_backend_health() -> bool:
    """Return True if the backend /health endpoint responds with 200."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return resp.status_code == 200
    except requests.RequestException:
        return False

def main() -> None:
    st.set_page_config(
        page_title="Collaborative Code Pad",
        layout="wide",
    )

    st.title("🧑‍💻 Collaborative Code Pad (Frontend Prototype)")

    if not check_backend_health():
        st.error(
            f"Backend is not reachable at {BACKEND_URL}. "
            "Please make sure the FastAPI server is running."
        )
        st.stop()

    # 1) Determine room id using backend as source of truth
    room_id = get_or_create_room_id_via_backend()

    # 2) Pull room state from backend and sync into session_state
    room, current_code = sync_room_into_session(room_id)

    with st.sidebar:
        st.subheader("Session")
        st.write(f"Room ID: `{room['room_id']}`")
        share_link = f"?room={room['room_id']}"
        st.caption("Share this URL suffix with your candidates:")
        st.code(share_link, language="text")

        st.subheader("Settings")

        lang_display_options = list(SUPPORTED_LANGUAGES.keys())
        # Find display label for current language
        current_display = next(
            (d for d, internal in SUPPORTED_LANGUAGES.items() if internal == room["language"]),
            "Python",
        )
        selected_display = st.selectbox(
            "Language",
            lang_display_options,
            index=lang_display_options.index(current_display),
        )
        selected_lang = normalize_language(selected_display)

        live_updates = st.checkbox(
            "Live updates (auto-refresh)",
            value=True,
            help="When enabled, this page will poll for updates every second.",
            key="live_updates",
        )

        st.markdown(
            """
            **Notes**

            - All users in the same room see the same code.
            - Last writer wins (changes propagate to everyone).
            - JavaScript code is executed in a sandboxed iframe.
            - Other languages are highlighted but not executed yet.
            - Room state is stored in the backend API.
            """
        )

    # If language changed, persist to backend
    if selected_lang != room["language"]:
        try:
            updated = update_room(room["room_id"], language=selected_lang)
            room = updated
        except requests.RequestException as exc:
            st.error(f"Failed to update language in backend: {exc}")

    st.write("### Shared code editor")
    st.info(
        "Changes are shared when you **leave the editor** (click outside) "
        "or press **Ctrl+Enter**. Other clients will see updates within about a second."
    )

    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("🧹 Clear editor", help="Remove all code and sync to backend"):
            st.session_state["code_editor"] = ""
            st.session_state["last_change_origin"] = "local"
            try:
                updated = update_room(room["room_id"], code="", language=selected_lang)
                st.session_state["code_version"] = updated["last_updated"]
            except requests.RequestException as exc:
                st.error(f"Failed to clear editor via backend: {exc}")

    new_code = st_ace(
        value=st.session_state.get("code_editor", ""),
        language=selected_lang,
        theme="xcode",
        wrap=True,
    )

    # Change detection logic
    if new_code != st.session_state.get("code_editor", ""):
        st.session_state["code_editor"] = new_code
        st.session_state["last_change_origin"] = "local"

        try:
            updated = update_room(
                room["room_id"],
                code=new_code,
                language=selected_lang,
            )
            st.session_state["code_version"] = updated["last_updated"]
        except requests.RequestException as exc:
            st.error(f"Failed to update code in backend: {exc}")

    col1, col2 = st.columns(2)

    with col1:
        st.write("#### Syntax-highlighted preview")
        st.code(st.session_state["code_editor"], language=selected_lang)

    with col2:
        st.write("#### In-browser execution")

        if selected_lang == "javascript":
            if st.button("▶ Run JavaScript in sandbox"):
                iframe_html = build_js_execution_iframe(st.session_state["code_editor"])
                components.html(iframe_html, height=300)
        else:
            st.info(
                f"Execution is only implemented for JavaScript at the moment. "
                f"Selected language: **{selected_lang}**"
            )

    st.caption(
        f"Last updated at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(room['last_updated']))}"
    )

    # 3) Polling for near real-time updates (still works with backend)
    if st.session_state.get("live_updates"):
        time.sleep(1.0)
        st.rerun()


if __name__ == "__main__":
    main()
