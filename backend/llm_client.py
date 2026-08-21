"""
Thin wrapper around the Groq client so every node calls the model the same
way (shared seed + temperature, both configurable via env vars) and every
call site is one line, not a re-implementation of message construction.

Swap-in note: Groq's chat completions API is what's wired up here. Unlike
Anthropic's API, Groq accepts a literal `seed` parameter, so GRAPH_SEED is
passed straight through instead of just being logged for reference. Seed
alone does not guarantee identical output between runs on most providers
(model/infra updates can shift results even with the same seed), but it
keeps runs as reproducible as the provider allows, which is what a fixed
seed is for.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from groq import Groq

_client: Groq | None = None


def _get_client(api_key: str | None = None) -> Groq:
    """
    Return a Groq client.

    If `api_key` is supplied (a per-user key sent from the frontend) a
    fresh, one-off client is built for it -- it is never cached or reused
    across requests/users. Otherwise fall back to a single process-wide
    client built from the server's own GROQ_API_KEY env var (useful for
    local dev / self-hosting with a shared key).
    """
    if api_key:
        return Groq(api_key=api_key)

    global _client
    if _client is None:
        _client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return _client


def model_settings() -> dict[str, Any]:
    return {
        "model": os.environ.get("LLM_MODEL", "openai/gpt-oss-120b"),
        # Raised from a fixed 0 so segment/subtopic wording varies instead
        # of reading stiff and repetitive -- still low enough to stay
        # on-topic and keep the JSON structure the prompts demand. Override
        # with LLM_TEMPERATURE in .env if you want it higher/lower.
        "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7")),
        "seed": int(os.environ.get("GRAPH_SEED", "20260812")),
    }


def call_llm_json(prompt: str, max_tokens: int = 2000, api_key: str | None = None) -> Any:
    """
    Call the model with a prompt that demands a JSON-only response, and
    parse it. Raises ValueError with the raw text if parsing fails, so the
    caller's log entry captures what actually came back.

    `api_key`, when provided, is a per-user key (e.g. entered by the user
    in the frontend and threaded through the graph state) and takes
    precedence over the server's own GROQ_API_KEY env var.
    """
    settings = model_settings()
    client = _get_client(api_key)

    response = client.chat.completions.create(
        model=settings["model"],
        max_tokens=max_tokens,
        temperature=settings["temperature"],
        seed=settings["seed"],
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content or ""
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {text}") from exc
