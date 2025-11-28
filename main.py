"""Anony: lightweight Grok 4.1 Fast chatbot via OpenRouter."""

from __future__ import annotations

import os
import sys
from typing import Final

import requests


API_URL: Final[str] = "https://openrouter.ai/api/v1/chat/completions"
MODEL: Final[str] = "x-ai/grok-4.1-fast"
MAX_MESSAGES: Final[int] = 12  # user+assistant pairs => last 6 chats
SYSTEM_PROMPT: Final[str] = (
    "You are Anony, a discreet AI friend with a lightly funny human touch. "
    "Keep replies helpful, respectful, and just a bit cheeky."
)


class ChatError(RuntimeError):
    """Represents failures while communicating with the OpenRouter API."""


def require_api_key() -> str:
    """Fetch the OpenRouter API key from the environment or exit with guidance."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ChatError(
            "Missing OPENROUTER_API_KEY environment variable. "
            "Create a key at https://openrouter.ai/settings/keys and export it "
            "before running this script."
        )
    return api_key


def ask_grok(prompt: str, history: list[dict[str, str]] | None = None) -> str:
    """Send a prompt to Grok 4.1 Fast with optional history context."""

    api_key = require_api_key()
    trimmed_history = list(history or [])[-MAX_MESSAGES:]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *trimmed_history,
        {"role": "user", "content": prompt},
    ]
    headers = {
        "Authorization": f"Bearer {api_key}",
        # Optional but recommended so your app shows up correctly inside OpenRouter.
        "HTTP-Referer": "https://example.com/anony",
        "X-Title": "Anony CLI",
    }
    payload = {
        "model": MODEL,
        "messages": messages[-MAX_MESSAGES:],
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
        raise ChatError(f"Unexpected API response: {data}") from exc


def repl() -> None:
    """Run a REPL that keeps the last six chats until you exit."""

    history: list[dict[str, str]] = []
    print("Anony (type 'exit' to quit)")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover - CLI nicety
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            reply = ask_grok(user_input, history)
        except ChatError as exc:
            print(f"Error: {exc}")
            continue
        except requests.HTTPError as exc:
            print(f"HTTP error: {exc.response.text}")
            continue

        print(f"Grok: {reply}\n")
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": reply})
        history = history[-MAX_MESSAGES:]


def main() -> int:
    try:
        repl()
    except ChatError as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
