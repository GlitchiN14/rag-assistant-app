"""Thin wrapper around the backend API. The URL comes from the environment."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
REQUEST_TIMEOUT = 180  # local LLMs can be slow on the first request


class ApiError(Exception):
    """An error with a message that is safe to show to the user."""


def _require_base_url() -> str:
    if not API_BASE_URL:
        raise ApiError("API_BASE_URL is not set. Copy .env.example to .env and set it.")
    return API_BASE_URL


def check_health() -> dict | None:
    """Return the /health payload, or None if the backend is unreachable."""
    try:
        r = requests.get(f"{_require_base_url()}/health", timeout=5)
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ApiError):
        return None


def ask(question: str) -> dict:
    """POST /query -> {"answer": str, "sources": [str]}. Raises ApiError on failure."""
    base = _require_base_url()
    try:
        r = requests.post(f"{base}/query", json={"question": question}, timeout=REQUEST_TIMEOUT)
    except requests.ConnectionError:
        raise ApiError(f"Can't reach the backend at {base}. Is it running?") from None
    except requests.Timeout:
        raise ApiError("The request timed out. The model may still be loading - try again.") from None

    if r.status_code == 422:
        raise ApiError("Please enter a valid question (3 to 1000 characters).")
    if r.status_code == 503:
        detail = r.json().get("detail", "The language model is unavailable.")
        raise ApiError(detail)
    if not r.ok:
        raise ApiError(f"The backend returned an error (HTTP {r.status_code}).")
    return r.json()
