"""
Wires the Lecture-Assistant graph:

  input -> search -> extract -> author_prioritization -> synthesis
        -> [HITL: plan_review] -> [HITL: fact_verification]
        -> refinement -> final_brief -> formatting -> END

Both bracketed nodes call langgraph.types.interrupt(), so the compiled graph
genuinely pauses at each and can only continue via a Command(resume=...)
delivered through the FastAPI /resume endpoint. A MemorySaver checkpointer
persists state across the pause so `/resume` can pick a paused run back up
by thread_id.
"""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from backend.graph.nodes.author_prioritization_node import author_prioritization_node
from backend.graph.nodes.extract_node import extract_node
from backend.graph.nodes.fact_verification_node import fact_verification_node
from backend.graph.nodes.final_brief_node import final_brief_node
from backend.graph.nodes.formatting_node import formatting_node
from backend.graph.nodes.hitl_plan_review_node import hitl_plan_review_node
from backend.graph.nodes.input_node import input_node
from backend.graph.nodes.refinement_node import refinement_node
from backend.graph.nodes.search_node import search_node
from backend.graph.nodes.synthesis_node import synthesis_node
from backend.graph.state import LectureState

_checkpointer = MemorySaver()


def build_graph():
    graph = StateGraph(LectureState)

    graph.add_node("input", input_node)
    graph.add_node("search", search_node)
    graph.add_node("extract", extract_node)
    graph.add_node("author_prioritization", author_prioritization_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("plan_review", hitl_plan_review_node)
    graph.add_node("fact_verification", fact_verification_node)
    graph.add_node("refinement", refinement_node)
    graph.add_node("final_brief", final_brief_node)
    graph.add_node("formatting", formatting_node)

    graph.set_entry_point("input")
    graph.add_edge("input", "search")
    graph.add_edge("search", "extract")
    graph.add_edge("extract", "author_prioritization")
    graph.add_edge("author_prioritization", "synthesis")
    graph.add_edge("synthesis", "plan_review")
    graph.add_edge("plan_review", "fact_verification")
    graph.add_edge("fact_verification", "refinement")
    graph.add_edge("refinement", "final_brief")
    graph.add_edge("final_brief", "formatting")
    graph.add_edge("formatting", END)

    return graph.compile(checkpointer=_checkpointer)


# Single compiled instance reused across requests; MemorySaver keeps each
# thread_id's paused state isolated.
compiled_graph = build_graph()
