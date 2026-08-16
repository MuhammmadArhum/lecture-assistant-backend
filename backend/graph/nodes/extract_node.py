"""Extract Node: pulls discrete, source-attributed claims from search results."""
from __future__ import annotations

import re
import uuid

from backend.graph.state import LectureState
from backend.llm_client import call_llm_json, model_settings
from backend.logging_utils import log_node_run

PROMPT_PATH = "backend/prompts/extract_prompt.txt"

# Cap on a single fallback claim's length, and on how many raw search
# results the fallback will turn into claims. Real (LLM-extracted) claims
# are already short, single sentences by construction of the prompt --
# this only bounds the *fallback* path, which otherwise used raw page
# scrape (nav menus, bylines, ad copy, markdown artifacts) verbatim.
_FALLBACK_SNIPPET_MAX_CHARS = 320


def _clean_snippet(raw: str) -> str:
    """Strip markdown/scrape artifacts from a raw search-result snippet and
    cut it down to one clean, presentation-sized chunk. This is what a raw
    Tavily result looks like before cleanup: markdown headers ('### ...'),
    truncation marks ('[...]'), byline lines, and multiple runs of
    whitespace from stripped HTML -- none of that belongs on a slide."""
    text = raw or ""
    text = re.sub(r"\[\.\.\.\]", " ", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= _FALLBACK_SNIPPET_MAX_CHARS:
        return text
    truncated = text[:_FALLBACK_SNIPPET_MAX_CHARS]
    # Prefer cutting at the last sentence boundary in range so it doesn't
    # end mid-word/mid-clause.
    last_period = truncated.rfind(". ")
    if last_period > _FALLBACK_SNIPPET_MAX_CHARS * 0.4:
        return truncated[:last_period + 1]
    return truncated.rsplit(" ", 1)[0] + "..."


def extract_node(state: LectureState) -> dict:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    search_results_text = "\n".join(
        f"- {r['title']} ({r['url']}): {r['content']}"
        for r in state.get("raw_search_results", [])
    )

    prompt = template.format(
        topic=state["topic"],
        audience=state["audience"],
        search_results=search_results_text,
    )

    try:
        raw_claims = call_llm_json(prompt, api_key=state.get("groq_api_key"))
        error_text = None
    except Exception as exc:
        # Deterministic offline fallback so the graph is runnable without a
        # live API key -- builds claims from ALL deduped search results
        # (not just the first 6), and cleans each snippet down to one
        # presentation-sized chunk instead of using raw page scrape.
        raw_claims = [
            {
                "text": _clean_snippet(r["content"]),
                "source_title": r["title"],
                "source_url": r["url"],
                "author": "unknown",
            }
            for r in state.get("raw_search_results", [])
            if r.get("content", "").strip()
        ]
        error_text = f"{type(exc).__name__}: {exc}"

    claims = [
        {
            "id": str(uuid.uuid4())[:8],
            "text": c["text"],
            "source_title": c["source_title"],
            "source_url": c["source_url"],
            "author": c.get("author") or "unknown",
            "credibility_score": 0.0,
            "verified": False,
            "verification_note": None,
        }
        for c in raw_claims
    ]

    output = {"extracted_claims": claims}
    settings = model_settings()

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="extract_node",
        inputs={"result_count": len(state.get("raw_search_results", []))},
        output={"claim_count": len(claims)},
        prompt_file=PROMPT_PATH,
        prompt_rendered=prompt,
        model=settings["model"],
        temperature=settings["temperature"],
        seed=settings["seed"],
        error=error_text,
    )

    return output