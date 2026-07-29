
"""Provide one isolated connection to the configured Claude model."""

import os
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


def call_model(
    system_prompt: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> Any:
    """Send messages and optional tools to Claude and return its response."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured.")

    client = Anthropic(api_key=api_key)

    request = {
        "model": model,
        "max_tokens": 800,
        "system": system_prompt,
        "messages": messages,
    }

    if tools:
        request["tools"] = tools

    return client.messages.create(**request)

