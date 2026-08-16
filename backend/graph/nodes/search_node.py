"""Search Node: runs web search queries for the lecture topic."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.logging_utils import log_node_run
from backend.search_client import web_search


def search_node(state: LectureState) -> dict:
    topic = state["topic"]
    queries = [
        topic,
        f"{topic} recent research",
        f"{topic} common misconceptions",
    ]

    results = []
    for q in queries:
        results.extend(web_search(q, max_results=3, api_key=state.get("tavily_api_key")))

    # de-duplicate by URL while preserving order
    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)

    output = {"raw_search_results": deduped}

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="search_node",
        inputs={"queries": queries},
        output={"result_count": len(deduped)},
    )

    return output
