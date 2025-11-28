"""Anony: Tiny Flask wrapper exposing the Grok chat via HTTP."""

from __future__ import annotations

import os
import uuid
from typing import Dict, Final, List

from flask import Flask, jsonify, make_response, request
import requests

API_URL: Final[str] = "https://openrouter.ai/api/v1/chat/completions"
MODEL: Final[str] = "x-ai/grok-4.1-fast"
MAX_MESSAGES: Final[int] = 12  # user+assistant pairs => last 6 chats
MAX_PROMPT_CHARS: Final[int] = 2000
SESSION_COOKIE_NAME: Final[str] = "anony_session"
SESSION_TTL_SECONDS: Final[int] = 60 * 60 * 24  # 24 hours
SYSTEM_PROMPT: Final[str] = (
    "You are Anony, a discreet AI friend with a lightly funny human touch. "
    "Keep replies helpful, respectful, and just a bit cheeky."
)

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Simple in-memory history store; replace with KV/Redis in production deployments.
HISTORY_STORE: Dict[str, List[dict[str, str]]] = {}


def require_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENROUTER_API_KEY env var. Set it or load from .env before running."
        )
    return api_key


def ask_grok(prompt: str, history: list[dict[str, str]] | None = None) -> str:
    headers = {
        "Authorization": f"Bearer {require_api_key()}",
        "HTTP-Referer": "https://example.com/anony",
        "X-Title": "Anony Web",
    }
    trimmed_history = list(history or [])[-MAX_MESSAGES:]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *trimmed_history,
        {"role": "user", "content": prompt},
    ]
    payload = {
        "model": MODEL,
        "messages": messages[-MAX_MESSAGES:],
    }
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def _get_session_id() -> tuple[str, bool]:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return session_id, False
    return uuid.uuid4().hex, True


def _attach_session_cookie(response, session_id: str, should_set: bool) -> tuple[str, bool]:
    if should_set:
        response.set_cookie(
            SESSION_COOKIE_NAME,
            session_id,
            max_age=SESSION_TTL_SECONDS,
            secure=True,
            httponly=True,
            samesite="Strict",
        )
    return session_id, should_set


def _load_history(session_id: str) -> List[dict[str, str]]:
    return list(HISTORY_STORE.get(session_id, []))


def _save_history(session_id: str, history: List[dict[str, str]]) -> None:
    HISTORY_STORE[session_id] = history[-MAX_MESSAGES:]


@app.route("/api/chat", methods=["POST"])
def chat():
    session_id, is_new = _get_session_id()
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        response = jsonify({"error": "prompt is required"})
        _attach_session_cookie(response, session_id, is_new)
        return response, 400
    if len(prompt) > MAX_PROMPT_CHARS:
        response = jsonify({"error": "prompt too long"})
        _attach_session_cookie(response, session_id, is_new)
        return response, 413
    try:
        history = _load_history(session_id)
        answer = ask_grok(prompt, history)
    except requests.HTTPError as exc:
        response = jsonify({"error": exc.response.text})
        _attach_session_cookie(response, session_id, is_new)
        return response, 502
    except Exception as exc:  # pragma: no cover - defensive
        response = jsonify({"error": str(exc)})
        _attach_session_cookie(response, session_id, is_new)
        return response, 500
    history.extend(
        [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ]
    )
    _save_history(session_id, history)
    response = jsonify({"answer": answer})
    _attach_session_cookie(response, session_id, is_new)
    return response


@app.route("/api/reset", methods=["POST"])
def reset():
    session_id, is_new = _get_session_id()
    HISTORY_STORE.pop(session_id, None)
    response = jsonify({"status": "ok"})
    _attach_session_cookie(response, session_id, is_new)
    return response


@app.route("/")
def root():
    session_id, is_new = _get_session_id()
    response = make_response(app.send_static_file("index.html"))
    _attach_session_cookie(response, session_id, is_new)
    return response


@app.after_request
def set_security_headers(response):
    csp = " ".join(
        [
            "default-src 'self';",
            "script-src 'self';",
            "style-src 'self' 'unsafe-inline';",
            "connect-src 'self';",
            "img-src 'self' data:;",
            "font-src 'self';",
            "frame-ancestors 'none';",
        ]
    )
    response.headers.setdefault("Content-Security-Policy", csp)
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
