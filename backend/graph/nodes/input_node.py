"""Input Node: validates and normalizes the user's lecture request."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.logging_utils import log_node_run


def input_node(state: LectureState) -> dict:
    topic = state.get("topic", "").strip()
    audience = state.get("audience", "").strip() or "general adult audience, no prior background assumed"
    target_minutes = state.get("target_minutes") or 45

    if not topic:
        raise ValueError("A lecture topic is required.")

    output = {"topic": topic, "audience": audience, "target_minutes": target_minutes}

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="input_node",
        inputs={"raw_topic": state.get("topic"), "raw_audience": state.get("audience")},
        output=output,
    )

    return output
