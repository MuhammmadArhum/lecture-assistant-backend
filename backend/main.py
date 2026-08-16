"""
FastAPI entry point for the Lecture-Assistant Agent.

Run with:  uvicorn backend.main:app --reload
"""
from __future__ import annotations

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel

load_dotenv()

from backend.export.pptx_builder import build_pptx  # noqa: E402
from backend.graph.build_graph import compiled_graph  # noqa: E402
from backend.logging_utils import read_run_log  # noqa: E402

app = FastAPI(title="Lecture-Assistant Agent")

# FRONTEND_ORIGIN accepts one or more comma-separated origins, e.g.
# "https://your-app.vercel.app,http://localhost:3000" -- handy since Vercel
# gives every deployment (prod + previews) its own URL.
_frontend_origins = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRunRequest(BaseModel):
    topic: str
    audience: str = ""
    target_minutes: int = 45
    # Per-user keys entered in the frontend. Never written to disk -- they
    # only live in this request and in the in-memory graph checkpoint for
    # the lifetime of the run.
    groq_api_key: str | None = None
    tavily_api_key: str | None = None


class ResumeRequest(BaseModel):
    thread_id: str
    status: str
    notes: str | None = None
    accepted_ids: list[str] | None = None


def _extract_interrupt(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    # langgraph wraps the interrupt() payload in an Interrupt object
    first = interrupts[0]
    return first.value if hasattr(first, "value") else first


def _run_response(thread_id: str, result: dict) -> dict:
    pending = _extract_interrupt(result)
    if pending is not None:
        return {"thread_id": thread_id, "status": "paused", "interrupt": pending}
    return {
        "thread_id": thread_id,
        "status": "complete",
        "final_brief": result.get("final_brief"),
        "formatted_brief_markdown": result.get("formatted_brief_markdown"),
    }


@app.post("/runs")
def start_run(req: StartRunRequest):
    groq_key = req.groq_api_key or os.environ.get("GROQ_API_KEY")
    if not groq_key:
        raise HTTPException(
            status_code=400,
            detail="No Groq API key was provided. Add your own key in the app's "
            "API settings, or set GROQ_API_KEY on the server.",
        )

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = compiled_graph.invoke(
        {
            "topic": req.topic,
            "audience": req.audience,
            "target_minutes": req.target_minutes,
            "thread_id": thread_id,
            "groq_api_key": req.groq_api_key,
            "tavily_api_key": req.tavily_api_key,
        },
        config=config,
    )

    return _run_response(thread_id, result)


@app.post("/resume")
def resume_run(req: ResumeRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    decision = {"status": req.status, "notes": req.notes}
    if req.accepted_ids is not None:
        decision["accepted_ids"] = req.accepted_ids

    try:
        result = compiled_graph.invoke(Command(resume=decision), config=config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not resume run: {exc}") from exc

    return _run_response(req.thread_id, result)


@app.get("/runs/{thread_id}")
def get_run_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = compiled_graph.get_state(config)
    if snapshot is None or snapshot.values is None:
        raise HTTPException(status_code=404, detail="Unknown thread_id")
    return {"thread_id": thread_id, "values": snapshot.values, "next": snapshot.next}


@app.get("/logs/{thread_id}")
def get_logs(thread_id: str):
    return {"thread_id": thread_id, "entries": read_run_log(thread_id)}


@app.post("/export/pptx")
def export_pptx(brief: dict):
    buffer = build_pptx(brief)
    filename = "lecture-brief.pptx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
