"""Synthesis Node: turns prioritized claims into a draft lecture plan."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.llm_client import call_llm_json, model_settings
from backend.logging_utils import log_node_run

PROMPT_PATH = "backend/prompts/synthesis_prompt.txt"


_GENERIC_SEGMENT_LABELS = [
    "Overview and context",
    "Core concepts",
    "Mechanisms and detail",
    "Applications and examples",
    "Open questions and discussion",
]


def _fallback_plan(target_minutes: int, topic: str, claims: list[dict]) -> dict:
    """Deterministic offline fallback used only when the LLM call raises.
    Built entirely from THIS run's actual claims/topic -- never canned
    content about an unrelated example topic -- so a fallback deck is
    always about what was actually requested, just less polished than an
    LLM-authored plan would be."""
    if not claims:
        # No search/extraction results at all: nothing to build slides
        # from. Say so plainly rather than inventing off-topic content.
        segment = {
            "label": f"{topic}: no sourced content available",
            "minutes": max(1, target_minutes),
            "notes": "No verified sources were retrieved for this topic in this run.",
            "subtopics": [{
                "title": "Why this segment is empty",
                "content": (
                    f"The Search/Extract nodes did not return any usable claims for "
                    f"\"{topic}\" in this run, so there is no sourced content to "
                    "build a plan from. Re-run once sources are available."
                ),
            }],
        }
        return {"segments": [segment], "rationale": "No sourced claims were available for this topic."}

    n_segments = min(len(_GENERIC_SEGMENT_LABELS), max(1, -(-len(claims) // 3)))
    labels = _GENERIC_SEGMENT_LABELS[:n_segments]

    # Round-robin claims into segments so every segment's subtopics are
    # genuine, sourced content -- not generic filler.
    buckets: list[list[dict]] = [[] for _ in range(n_segments)]
    for i, claim in enumerate(claims):
        buckets[i % n_segments].append(claim)

    minutes_per_segment = max(1, round(target_minutes / n_segments))
    segments = []
    for label, bucket in zip(labels, buckets):
        if not bucket:
            continue
        subtopics = [
            {"title": c.get("source_title") or f"{topic} — {label}", "content": c["text"]}
            for c in bucket
        ]
        segments.append({
            "label": f"{topic}: {label}",
            "minutes": minutes_per_segment,
            "notes": f"Covers {label.lower()} for {topic}, drawn from {len(bucket)} sourced claim(s).",
            "subtopics": subtopics,
        })

    return {
        "segments": segments,
        "rationale": f"Segments built directly from sourced claims about {topic}, grouped in retrieval order.",
    }


def _max_tokens_for(target_minutes: int) -> int:
    # Longer lectures need proportionally more subtopics, which means a
    # bigger JSON response -- without this, synthesis for a 60-minute
    # lecture gets truncated mid-JSON and either fails or silently drops
    # subtopics for later segments.
    return min(8000, 2000 + target_minutes * 60)


def synthesis_node(state: LectureState) -> dict:
    claims = state.get("prioritized_claims", [])
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    claims_text = "\n".join(
        f"[{c['credibility_score']}] {c['text']} (source: {c['source_title']})" for c in claims
    )
    prompt = template.format(
        target_minutes=state["target_minutes"],
        topic=state["topic"],
        audience=state["audience"],
        claims=claims_text,
    )

    try:
        result = call_llm_json(
            prompt,
            max_tokens=_max_tokens_for(state["target_minutes"]),
            api_key=state.get("groq_api_key"),
        )
        error_text = None
    except Exception as exc:
        result = _fallback_plan(state["target_minutes"], state["topic"], claims)
        error_text = f"{type(exc).__name__}: {exc}"

    output = {
        "draft_plan": result["segments"],
        "draft_plan_rationale": result.get("rationale", ""),
    }
    settings = model_settings()

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="synthesis_node",
        inputs={"claim_count": len(claims)},
        output=output,
        prompt_file=PROMPT_PATH,
        prompt_rendered=prompt,
        model=settings["model"],
        temperature=settings["temperature"],
        seed=settings["seed"],
        error=error_text,
    )

    return output