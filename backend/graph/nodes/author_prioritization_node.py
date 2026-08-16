"""Author-Prioritization Node: scores each claim's source for credibility."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.llm_client import call_llm_json, model_settings
from backend.logging_utils import log_node_run

PROMPT_PATH = "backend/prompts/author_prioritization_prompt.txt"

_TRUSTED_DOMAIN_HINTS = (".edu", ".gov", "nature.com", "si.edu", "ieee", "santafe.edu")


def _fallback_score(claim: dict) -> float:
    url = claim.get("source_url", "")
    has_author = claim.get("author", "unknown") != "unknown"
    domain_trust = any(hint in url for hint in _TRUSTED_DOMAIN_HINTS)
    return round(min(1.0, 0.4 + (0.3 if has_author else 0) + (0.3 if domain_trust else 0)), 2)


def author_prioritization_node(state: LectureState) -> dict:
    claims = state.get("extracted_claims", [])
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    claims_text = "\n".join(
        f"id={c['id']} | author={c['author']} | source={c['source_title']} ({c['source_url']}) | claim={c['text']}"
        for c in claims
    )
    prompt = template.format(topic=state["topic"], claims=claims_text)

    try:
        scores = {
            s["id"]: float(s["credibility_score"])
            for s in call_llm_json(prompt, api_key=state.get("groq_api_key"))
        }
    except Exception:
        scores = {c["id"]: _fallback_score(c) for c in claims}

    prioritized = sorted(
        (
            {**c, "credibility_score": scores.get(c["id"], _fallback_score(c))}
            for c in claims
        ),
        key=lambda c: c["credibility_score"],
        reverse=True,
    )

    output = {"prioritized_claims": prioritized}
    settings = model_settings()

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="author_prioritization_node",
        inputs={"claim_count": len(claims)},
        output={"top_score": prioritized[0]["credibility_score"] if prioritized else None},
        prompt_file=PROMPT_PATH,
        prompt_rendered=prompt,
        model=settings["model"],
        temperature=settings["temperature"],
        seed=settings["seed"],
    )

    return output
