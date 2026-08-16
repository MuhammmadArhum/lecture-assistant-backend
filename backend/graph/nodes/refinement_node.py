"""Refinement Node: incorporates both HITL checkpoints' decisions into a revised plan."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.llm_client import call_llm_json, model_settings
from backend.logging_utils import log_node_run

PROMPT_PATH = "backend/prompts/refine_prompt.txt"


def refinement_node(state: LectureState) -> dict:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    verified = [c for c in state.get("claims_for_verification", []) if c["verified"]]

    prompt = template.format(
        draft_plan=state.get("draft_plan", []),
        plan_review_status=state.get("plan_review_status"),
        plan_review_notes=state.get("plan_review_notes") or "(none)",
        fact_check_status=state.get("fact_check_status"),
        fact_check_notes=state.get("fact_check_notes") or "(none)",
        verified_claims="\n".join(f"- {c['text']} ({c['source_title']})" for c in verified),
    )

    try:
        # Scale the token budget with lecture length -- same reasoning as
        # synthesis_node: more minutes -> more subtopics -> bigger JSON.
        max_tokens = min(8000, 2000 + (state.get("target_minutes") or 45) * 60)
        result = call_llm_json(prompt, max_tokens=max_tokens, api_key=state.get("groq_api_key"))
        refined_plan = result["segments"]
    except Exception:
        # Offline fallback: keep the draft plan, just relabel if reworked.
        refined_plan = state.get("draft_plan", [])
        if state.get("plan_review_status") == "restructure":
            refined_plan = list(reversed(refined_plan))

    output = {"refined_plan": refined_plan}
    settings = model_settings()

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="refinement_node",
        inputs={
            "plan_review_status": state.get("plan_review_status"),
            "fact_check_status": state.get("fact_check_status"),
            "verified_claim_count": len(verified),
        },
        output={"segment_count": len(refined_plan)},
        prompt_file=PROMPT_PATH,
        prompt_rendered=prompt,
        model=settings["model"],
        temperature=settings["temperature"],
        seed=settings["seed"],
    )

    return output