from __future__ import annotations

import socket
import threading
import time
from typing import Generator

import pytest
import requests
import uvicorn

from src.app_backend.main import app
from src.app_frontend import api_client


def _wait_for_port(host: str, port: int, timeout: float = 5.0) -> None:
    """Block until `host:port` is accepting TCP connections or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((host, port))
                return
            except OSError:
                time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for {host}:{port} to become available")


@pytest.fixture(scope="session")
def backend_server() -> Generator[str, None, None]:
    """
    Run the FastAPI backend in a background uvicorn server.

    Yields the base URL (e.g. http://127.0.0.1:8001) that tests can use.
    """
    host = "127.0.0.1"
    port = 8001
    base_url = f"http://{host}:{port}"

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
    )

    server = uvicorn.Server(config)

    def run() -> None:
        # This will block until server.should_exit is set to True
        server.run()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    # Wait until the port is accepting connections
    _wait_for_port(host, port)

    yield base_url

    # Shut down the server at the end of the test session
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def backend_env(monkeypatch: pytest.MonkeyPatch, backend_server: str) -> None:
    """
    Point the frontend API client to the running backend server by setting
    COLLAB_APP_BACKEND_URL and reloading the api_client module.
    """
    monkeypatch.setenv("COLLAB_APP_BACKEND_URL", backend_server)

    # Reload the module so BACKEND_URL picks up the new env var
    import importlib

    import src.app_frontend.api_client as client_module

    importlib.reload(client_module)

    # Update the reference in this file to use the reloaded module
    global api_client  # type: ignore[global-variable-not-assigned]
    api_client = client_module


def test_health_endpoint_reachable(backend_server: str) -> None:
    """Sanity check: the backend health endpoint should respond over HTTP."""
    resp = requests.get(f"{backend_server}/health", timeout=2)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_room_integration(backend_env: None) -> None:
    """
    End-to-end:
      - use frontend api_client.create_room()
      - read back with api_client.get_room()
    """
    created = api_client.create_room(code="print('hello')", language="python")
    room_id = created["room_id"]

    fetched = api_client.get_room(room_id)
    assert fetched is not None
    assert fetched["room_id"] == room_id
    assert fetched["code"] == "print('hello')"
    assert fetched["language"] == "python"


def test_update_room_integration(backend_env: None) -> None:
    """
    End-to-end:
      - create room
      - update via api_client.update_room()
      - verify via api_client.get_room()
    """
    created = api_client.create_room(code="initial", language="python")
    room_id = created["room_id"]

    updated = api_client.update_room(room_id, code="updated", language="javascript")
    assert updated["room_id"] == room_id
    assert updated["code"] == "updated"
    assert updated["language"] == "javascript"

    fetched = api_client.get_room(room_id)
    assert fetched is not None
    assert fetched["code"] == "updated"
    assert fetched["language"] == "javascript"


def test_two_clients_simulated_integration(backend_env: None) -> None:
    """
    Simulate two clients collaborating on the same room via the HTTP API:

      - Client A creates a room and writes some code
      - Client B fetches the room and sees A's code
      - Client B updates the code
      - Client A fetches again and sees B's update
    """
    # "Client A" creates the room
    room_a = api_client.create_room(code="client A code", language="python")
    room_id = room_a["room_id"]

    # "Client B" fetches same room
    room_b_view = api_client.get_room(room_id)
    assert room_b_view is not None
    assert room_b_view["code"] == "client A code"

    # "Client B" updates the code
    room_b_updated = api_client.update_room(room_id, code="client B update")
    assert room_b_updated["code"] == "client B update"

    # "Client A" fetches again
    room_a_new_view = api_client.get_room(room_id)
    assert room_a_new_view is not None
    assert room_a_new_view["code"] == "client B update"
