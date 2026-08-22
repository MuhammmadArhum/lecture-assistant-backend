"""
Shared graph state for the Lecture-Assistant Agent.

Topic used throughout this scaffold's example content: "The Hidden Engineering
of Ant Colonies" -- an original topic invented for this build, unrelated to
any example in the source assignment document.
"""
from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict


class SourceClaim(TypedDict):
    """A single extracted factual claim tied back to a source."""
    id: str
    text: str
    source_title: str
    source_url: str
    author: Optional[str]
    credibility_score: float  # 0-1, set by the Author-Prioritization Node
    verified: bool
    verification_note: Optional[str]


class Subtopic(TypedDict):
    """One slide's worth of real content within a segment. Segments are
    named chunks of the lecture (e.g. "Front-end vs back-end"); subtopics
    are the individual talking points inside that chunk, generated so that
    a longer segment (more minutes) yields proportionally more subtopics --
    this is what gives each dynamically-added slide actual content instead
    of an empty body."""
    title: str
    content: str


class PlanSegment(TypedDict):
    label: str
    minutes: int
    notes: str
    subtopics: list[Subtopic]


class NodeLogEntry(TypedDict):
    timestamp: str
    node: str
    inputs_summary: str
    prompt_file: Optional[str]
    prompt_rendered: Optional[str]
    output_summary: str
    model: Optional[str]
    temperature: Optional[float]
    seed: Optional[int]
    human_decision: Optional[str]


class FinalBrief(TypedDict, total=False):
    title: str
    introduction: str
    summary: str
    key_findings: list[dict[str, str]]   # [{ "text": ..., "citation": ... }]
    risks: list[str]
    further_reading: list[dict[str, str]]  # [{ "title": ..., "url": ... }]
    node_trace: list[NodeLogEntry]
    target_minutes: int          # carried through for dynamic pptx sizing
    segments: list[PlanSegment]  # copy of refined_plan, one slide group per segment


class LectureState(TypedDict, total=False):
    # --- Input Node ---
    topic: str
    audience: str
    target_minutes: int

    # --- Search Node ---
    raw_search_results: list[dict[str, Any]]

    # --- Extract Node ---
    extracted_claims: list[SourceClaim]

    # --- Author-Prioritization Node ---
    prioritized_claims: list[SourceClaim]

    # --- Synthesis Node ---
    draft_plan: list[PlanSegment]
    draft_plan_rationale: str

    # --- HITL: Plan Review ---
    plan_review_status: Literal["pending", "approved", "rework", "more_sources"]
    plan_review_notes: Optional[str]

    # --- HITL: Fact Verification ---
    claims_for_verification: list[SourceClaim]
    fact_check_status: Literal["pending", "approved", "flagged"]
    fact_check_notes: Optional[str]

    # --- Refinement Node ---
    refined_plan: list[PlanSegment]

    # --- Final Brief Node ---
    final_brief: FinalBrief

    # --- Formatting Node ---
    formatted_brief_markdown: str

    # --- Orchestration ---
    node_trace: list[NodeLogEntry]
    thread_id: str
    status: str

    # --- User-supplied API keys (per-request, never persisted to disk) ---
    groq_api_key: Optional[str]
    tavily_api_key: Optional[str]

    # --- Gamma-style one-shot mode ---
    # When true, the two HITL checkpoint nodes below auto-fill the
    # "everything looks good" decision instead of calling interrupt(), so
    # the whole graph runs start-to-finish without pausing. Off by default
    # -- the real human-in-the-loop review is still the default behavior.
    auto_approve: Optional[bool]

    # --- Selected deck theme (see backend/themes.py), used at export time ---
    theme: Optional[str]
