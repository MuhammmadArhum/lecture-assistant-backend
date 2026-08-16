"""Formatting Node (optional): renders the final brief as clean Markdown."""
from __future__ import annotations

from backend.graph.state import LectureState
from backend.logging_utils import log_node_run


def formatting_node(state: LectureState) -> dict:
    brief = state.get("final_brief", {})

    lines = [f"# {brief.get('title', 'Untitled Lecture')}", ""]
    lines += ["## Introduction", brief.get("introduction", ""), ""]
    lines += ["## Summary", brief.get("summary", ""), ""]
    lines += ["## Key Findings"]
    for kf in brief.get("key_findings", []):
        lines.append(f"- {kf['text']} — *{kf['citation']}*")
    lines += ["", "## Risks"]
    for r in brief.get("risks", []):
        lines.append(f"- {r}")
    lines += ["", "## Further Reading"]
    for fr in brief.get("further_reading", []):
        lines.append(f"- [{fr['title']}]({fr['url']})")

    markdown = "\n".join(lines)
    output = {"formatted_brief_markdown": markdown, "status": "complete"}

    log_node_run(
        thread_id=state.get("thread_id", "unknown"),
        node="formatting_node",
        inputs={"has_brief": bool(brief)},
        output={"markdown_length": len(markdown)},
    )

    return output
