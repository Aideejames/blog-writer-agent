"""FastAPI wrapper around the Blog Writer LangGraph agent."""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import blog_agent

# Load .env when running locally (Render uses env vars set in the dashboard)
load_dotenv()

app = FastAPI(
    title="Blog Writer Agent API",
    description=(
        "Multi-agent blog-writing pipeline: research → outline → write → edit. "
        "Built with LangGraph and Google Gemini."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production if you want
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Optional password gate ──────────────────────────────────
# If DEMO_PASSWORD is set, callers must supply it in the X-Demo-Password header.
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD")


def check_password(x_demo_password: str | None = Header(default=None)):
    if DEMO_PASSWORD is None:
        return  # no password set → open (dev mode)
    if x_demo_password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect or missing password")


# ── Schemas ────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)


class GenerateResponse(BaseModel):
    topic: str
    final_post: str
    research: str
    outline: str
    draft: str


# ── Routes ─────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Blog Writer Agent API",
        "docs": "/docs",
        "password_required": DEMO_PASSWORD is not None,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse, dependencies=[Depends(check_password)])
def generate(req: GenerateRequest):
    try:
        result = blog_agent.invoke({
            "topic": req.topic,
            "research": "",
            "outline": "",
            "draft": "",
            "final_post": "",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}")

    return GenerateResponse(
        topic=req.topic,
        final_post=result["final_post"],
        research=result["research"],
        outline=result["outline"],
        draft=result["draft"],
    )