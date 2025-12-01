"""
Abstractions for in-browser code execution.

In the final implementation, this module will define data structures and
protocols used between the frontend (Streamlit + JS/Pyodide) and the backend.
"""

from dataclasses import dataclass
from typing import Literal, Any, Dict

Language = Literal["python", "javascript", "sql"]  # extend as needed

@dataclass
class ExecutionRequest:
    language: Language
    code: str
    # additional fields later: stdin, timeouts, etc.


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    error: str | None
    metadata: Dict[str, Any]