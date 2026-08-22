"""
HITL Fact Verification Node.

Second real checkpoint: presents 3-6 extracted claims with sources and
pauses via interrupt() until the human resumes with a per-claim verdict.

Decision options (distinct wording from the source document's example):
  - "accept_all"     -> every shown claim is marked verified
  - "accept_subset"  -> only the claim ids listed in `accepted_ids` are verified;
                        the rest are dropped from downstream use
  - "send_back"      -> none accepted yet, free-text note routes back to Refinement
                        to request different/better-sourced claims
"""
from __future__ import annotations

from langgraph.types import interrupt

from backend.graph.state import LectureState
from backend.logging_utils import log_node_run


def fact_verification_node(state: LectureState) -> dict:
    claims_to_show = state.get("prioritized_claims", [])[:6]

    payload = {
        "checkpoint": "fact_verification",
        "claims": [
            {
                "id": c["id"],
                "text": c["text"],
                "source_title": c["source_title"],
                "source_url": c["source_url"],
                "credibility_score": c["credibility_score"],
            }
            for c in claims_to_show
        ],
        "options": [
            {"value": "accept_all", "label": "Accept all shown claims"},
            {"value": "accept_subset", "label": "Accept only selected claims"},
            {"value": "send_back", "label": "Send back for better sources"},
        ],
    }

    if state.get("auto_approve"):
        # Gamma-style one-shot mode: skip the pause and accept every shown
        # claim, same as a human picking "accept_all".
        decision = {"status": "accept_all", "notes": "Auto-approved (one-shot mode)"}
    else:
        decision = interrupt(payload)

    status = decision.get("status", "accept_all")
    notes = decision.get("notes")
    # Trust exactly what the client sent (the UI keeps this in sync with
    # the checkboxes for every action, including "accept_all" -- it no
    # longer needs a server-side override that could silently reintroduce
    # a claim the human explicitly unchecked). Only fall back to "every
    # shown claim" if a client doesn't send accepted_ids at all.
    accepted_ids = set(decision.get("accepted_ids", [c["id"] for c in claims_to_show]))
    if status == "send_back":
        accepted_ids = set()

    verified_claims = []
    for c in claims_to_show:
        is_verified = c["id"] in accepted_ids
        verified_claims.append({**c, "verified": is_verified, "verification_note": notes if not is_verified else None})

    output = {
        "claims_for_verification": verified_claims,
        "fact_check_status": "approved" if status != "send_back" else "flagged",
        "fact_check_notes": notes,
    }

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="fact_verification_node",
        inputs={"claims_shown": len(claims_to_show)},
        output={"accepted": len(accepted_ids), "status": status},
        human_decision=status,
    )

    return output
