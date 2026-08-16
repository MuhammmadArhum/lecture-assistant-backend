"""Final Brief Node: produces the fully-cited lecture brief structured for slides."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.llm_client import call_llm_json, model_settings
from backend.logging_utils import log_node_run

PROMPT_PATH = "backend/prompts/final_brief_prompt.txt"

# Simple keyword check so the offline fallback (and the LLM prompt) can honor
# a human reviewer telling Plan Review "no definition" / "skip the intro" --
# previously this was ignored entirely and an Introduction was always added.
_INTRO_EXCLUSION_HINTS = ("no definition", "no intro", "skip intro", "without intro", "no introduction")


def _notes_exclude_introduction(state: LectureState) -> bool:
    combined = f"{state.get('plan_review_notes') or ''} {state.get('fact_check_notes') or ''}".lower()
    return any(hint in combined for hint in _INTRO_EXCLUSION_HINTS)


def _fallback_brief(state: LectureState, verified: list[dict]) -> dict:
    # Only ever use claims the human actually verified -- never fall back to
    # the full unfiltered `claims_for_verification` list. Doing so used to
    # silently reintroduce claims the human had explicitly unchecked
    # whenever the LLM call failed and this fallback path ran.
    top = verified[:6]
    skip_intro = _notes_exclude_introduction(state)
    topic = state["topic"]
    # Build the summary from this run's actual top claims rather than a
    # canned unrelated example, so a fallback brief is always on-topic.
    summary_claims = [c["text"] for c in top[:3]]
    summary = (
        " ".join(summary_claims)
        if summary_claims
        else f"No verified sourced claims were available to summarize {topic} in this run."
    )
    return {
        "title": f"{topic}: A Working Lecture Brief",
        "introduction": "" if skip_intro else (
            f"This session introduces {topic.lower()} to {state['audience']}, "
            "grounding each claim in a cited source rather than folk explanation."
        ),
        "summary": summary,
        "key_findings": [
            {"text": c["text"], "citation": f"{c['source_title']} ({c['source_url']})"}
            for c in top
        ],
        "risks": [
            f"Over-generalizing findings from a limited set of sources to all of {topic}.",
            "Treating vendor or marketing claims as neutral, independently verified fact.",
            f"Audience unfamiliarity with {topic} terminology slowing the pace.",
        ],
        "further_reading": [
            {"title": c["source_title"], "url": c["source_url"]} for c in top
        ],
    }


def final_brief_node(state: LectureState) -> dict:
    verified = [c for c in state.get("claims_for_verification", []) if c["verified"]]

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.format(
        topic=state["topic"],
        audience=state["audience"],
        refined_plan=state.get("refined_plan", []),
        verified_claims="\n".join(f"- {c['text']} ({c['source_title']}, {c['source_url']})" for c in verified),
        plan_review_notes=state.get("plan_review_notes") or "(none)",
        fact_check_notes=state.get("fact_check_notes") or "(none)",
    )

    try:
        brief = call_llm_json(prompt, max_tokens=3000, api_key=state.get("groq_api_key"))
        # Belt-and-suspenders: even if the model ignored the instruction,
        # enforce the human's exclusion request deterministically.
        if _notes_exclude_introduction(state):
            brief["introduction"] = ""
        error_text = None
    except Exception as exc:
        brief = _fallback_brief(state, verified)
        error_text = f"{type(exc).__name__}: {exc}"

    brief["node_trace"] = state.get("node_trace", [])
    # Carried through so the pptx exporter can size the deck to the
    # requested lecture length and build one slide group per segment.
    brief["target_minutes"] = state.get("target_minutes")
    brief["segments"] = state.get("refined_plan", [])

    output = {"final_brief": brief}
    settings = model_settings()

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="final_brief_node",
        inputs={"verified_claim_count": len(verified)},
        output={"key_findings": len(brief.get("key_findings", []))},
        prompt_file=PROMPT_PATH,
        prompt_rendered=prompt,
        model=settings["model"],
        temperature=settings["temperature"],
        seed=settings["seed"],
        error=error_text,
    )

    return output