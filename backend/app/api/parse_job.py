"""
AI-powered job file parser.
Accepts CSV / PDF / DOCX uploads, extracts text, then calls Claude to
return structured job-posting fields ready to fill the Post Job form.
"""
import csv
import io
import json
import logging

import anthropic
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.api.applications import get_current_user
from app.api.employer import require_employer
from app.core.config import settings
from app.models.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employer", tags=["employer"])

ALLOWED_TYPES = {
    "text/csv",
    "application/csv",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

SYSTEM_PROMPT = """You are a job-posting data extractor. Given raw text from a job description document, extract and return ONLY a JSON object with these exact keys:

{
  "title": "job title string",
  "location": "city, state or Remote",
  "remote": true or false,
  "job_type": "full_time | part_time | contract | internship | temporary",
  "salary_min": number or null,
  "salary_max": number or null,
  "description": "main description text",
  "requirements": "requirements/qualifications text or null",
  "benefits": "benefits text or null",
  "skills": ["skill1", "skill2"],
  "industry": "technology | healthcare | finance | marketing | education | legal | engineering | logistics | manufacturing | retail"
}

Rules:
- salary_min / salary_max must be annual USD integers (e.g. 120000). Null if not mentioned.
- skills: array of individual skill strings, max 15 items.
- industry: pick the single best match from the list above.
- job_type: default to full_time if not specified.
- remote: true if role mentions remote, hybrid, or work from home.
- Return ONLY the JSON object, no markdown fences, no explanation."""


def _extract_text_csv(data: bytes) -> str:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return text
    parts = []
    for row in rows:
        parts.append("  ".join(f"{k}: {v}" for k, v in row.items() if v))
    return "\n".join(parts)


def _extract_text_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            pages.append(t)
    return "\n".join(pages)


def _extract_text_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_text(filename: str, content_type: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".csv") or content_type in ("text/csv", "application/csv"):
        return _extract_text_csv(data)
    if name.endswith(".pdf") or content_type == "application/pdf":
        return _extract_text_pdf(data)
    if name.endswith(".docx") or "wordprocessingml" in content_type:
        return _extract_text_docx(data)
    if name.endswith(".doc") or content_type == "application/msword":
        raise HTTPException(
            status_code=415,
            detail="Legacy .doc files are not supported. Please save as .docx or .pdf and try again.",
        )
    # plain text fallback
    return data.decode("utf-8", errors="replace")


def _parse_with_claude(text: str) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI parsing is not configured. Add ANTHROPIC_API_KEY to your .env file.",
        )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    # Truncate to ~12k chars to stay well within token limits
    truncated = text[:12000]

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Extract job data from this text:\n\n{truncated}"}],
    )

    raw = message.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned non-JSON: {raw[:200]}")
        raise HTTPException(status_code=502, detail=f"Could not parse AI response: {e}")


@router.post("/parse-job-file")
async def parse_job_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_employer),
):
    if file.size and file.size > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit.")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit.")

    content_type = file.content_type or ""
    filename = file.filename or ""

    try:
        text = _extract_text(filename, content_type, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Text extraction failed")
        raise HTTPException(status_code=422, detail=f"Could not read file: {e}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the file.")

    result = _parse_with_claude(text)
    return JSONResponse(content=result)
