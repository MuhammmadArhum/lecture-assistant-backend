"""
HITL Plan Review Node.

This is a REAL interrupt: execution genuinely halts here via LangGraph's
interrupt(), and the graph will not proceed until the FastAPI /resume
endpoint delivers a Command(resume=...) with the human's decision. There is
no timeout-based or auto-approve fallback.

Decision options presented to the human (distinct from the source
document's "Approve | More Sources | Emphasize Examples | Emphasize Ethics |
Rework" wording):
  - "confirm"        -> proceed as drafted
  - "broaden_sources" -> loop back for another search pass before refining
  - "restructure"    -> keep sources, ask Refinement to reshape segment order/timing
"""
from __future__ import annotations

from langgraph.types import interrupt

from backend.graph.state import LectureState
from backend.logging_utils import log_node_run


def hitl_plan_review_node(state: LectureState) -> dict:
    payload = {
        "checkpoint": "plan_review",
        "topic": state["topic"],
        "draft_plan": state["draft_plan"],
        "rationale": state.get("draft_plan_rationale", ""),
        "options": [
            {"value": "confirm", "label": "Confirm plan as drafted"},
            {"value": "broaden_sources", "label": "Search for more sources first"},
            {"value": "restructure", "label": "Keep sources, restructure segments"},
        ],
    }

    # Execution pauses here until /resume sends a decision.
    decision = interrupt(payload)

    status = decision.get("status", "confirm")
    notes = decision.get("notes")

    output = {"plan_review_status": status, "plan_review_notes": notes}

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="hitl_plan_review_node",
        inputs={"segments": len(state.get("draft_plan", []))},
        output=output,
        human_decision=status,
    )

    return output
