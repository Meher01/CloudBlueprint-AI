import os
import re

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")

app = FastAPI(title="CloudBlueprint AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN else [],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):517\d",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    title: str
    problem: str
    features: str = ""
    projectType: str = ""


async def query_ollama(
    prompt: str,
    temperature: float | None = None,
    num_predict: int = 900,
) -> str:
    options: dict[str, int | float] = {"num_predict": num_predict}
    if temperature is not None:
        options["temperature"] = temperature

    payload: dict[str, object] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach Ollama at {OLLAMA_URL}: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an invalid response.",
        ) from exc

    result = data.get("response") if isinstance(data, dict) else None
    if not isinstance(result, str) or not result.strip():
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an empty or invalid response.",
        )

    return result.strip()


def format_plan_as_plain_text(plan: str) -> str:
    section_names = {
        "project summary": "1. Project summary",
        "suggested features": "2. Suggested features",
        "aws architecture": "3. AWS architecture",
        "data flow": "4. Data flow",
        "security and privacy considerations": "5. Security and privacy considerations",
        "build phases": "6. Build phases",
    }

    lines = []

    for line in plan.splitlines():
        if re.match(r"^\s*```", line):
            continue

        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)

        if re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            continue

        line = re.sub(
            r"\*\*(.*?)\*\*|__(.*?)__",
            lambda match: match[1] or match[2],
            line,
        )
        line = re.sub(r"(?<!\w)(\*|_)([^*_]+)\1(?!\w)", r"\2", line)
        line = re.sub(r"`([^`]*)`", r"\1", line)
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", line)

        section_match = re.match(
            r"^\s*(?:\d+[.)]\s*)?"
            r"(Project summary|Suggested features|AWS architecture|Data flow|"
            r"Security and privacy considerations|Build phases)\s*:?\s*$",
            line,
            re.IGNORECASE,
        )

        if section_match:
            section_name = section_match.group(1).lower()
            lines.append(f"**{section_names[section_name]}**")
            continue

        line = re.sub(r"^(\s*)[-*+]\s+", r"\1• ", line)
        lines.append(line)

    return "\n".join(lines).strip()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "CloudBlueprint AI API"}


@app.post("/api/generate-plan")
async def generate_plan(request: PlanRequest):
    idea_text = f"{request.title} {request.problem}".strip()

    if not re.search(r"[^\W\d_]", idea_text, re.UNICODE):
        raise HTTPException(
            status_code=422,
            detail="Please enter at least one meaningful word.",
        )

    classification = await query_ollama(
        f"""
You check only whether user input is intelligible language. Do not judge
whether it is a good project idea, relevant to AWS, or a complete sentence.
Reply VALID for any recognizable word or understandable phrase, even if it is
only one word. If uncertain, reply VALID.
Reply INVALID only when the input is clearly unintelligible random characters
or numbers/symbols with no recognizable word.

Examples:
- "weather" -> VALID
- "cat" -> VALID
- "AWS" -> VALID
- "asdfgh" -> INVALID
- "qzxv" -> INVALID
- "123456" -> INVALID

Title: {request.title}
Problem: {request.problem}

Reply with exactly one word: VALID or INVALID.
""",
        temperature=0,
        num_predict=8,
    )

    decision = re.search(r"\b(VALID|INVALID)\b", classification.upper())

    if decision is None:
        raise HTTPException(
            status_code=502,
            detail="Ollama could not validate the input. Please try again.",
        )

    if decision.group(1) == "INVALID":
        raise HTTPException(
            status_code=422,
            detail="The input appears unintelligible. Please enter meaningful words.",
        )

    prompt = f"""
You are CloudBlueprint AI, an assistant that designs practical AWS architectures.
Create a concise project plan based on the user's idea.

Project title: {request.title}
Problem: {request.problem}
Who will use it and where: {request.projectType or "Not specified"}
Requested features: {request.features or "None specified"}

Return these sections:
1. Project summary
2. Suggested features
3. AWS architecture
4. Data flow
5. Security and privacy considerations
6. Build phases

Use only AWS services in the architecture. Mention tradeoffs and avoid claiming the plan is production-ready.

Formatting requirements:
- Put each section label on its own line, exactly as listed above.
- Put the section content on the following lines, not beside the label.
- Use short paragraphs and bullet points to keep the plan easy to scan.
- Use • at the start of each list item.
- Do not use Markdown headings, bold, italics, code fences, or links. The app will style only the six section labels.
"""

    plan = format_plan_as_plain_text(
        await query_ollama(prompt, temperature=0.3, num_predict=900)
    )

    return {
        "plan": plan,
        "model": OLLAMA_MODEL,
    }