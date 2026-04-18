"""Gemini AI transaction parser — unified async pipeline with intent detection."""

from __future__ import annotations

import base64
import json
import logging
import re
from datetime import date
from typing import Any

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy Gemini client — created on first use
_client = None
MODEL_NAME = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    """Get or create the Gemini client (lazy init)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


# ─── Unified Prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen moliyaviy yordamchi AI san. Foydalanuvchi xabarining MAQSADINI (intent) aniqlab, tegishli ma'lumotlarni yig'ishing kerak.

TILLAR: O'zbek (barcha shevalar), Rus (разговорный), Ingliz.
SANA: Bugungi sana: {today}

1. INTENT TURLARI:
   - "transaction": Foydalanuvchi harajat yoki daromad kiritmoqda. (Masalan: "50k ovqatga", "3 mln oylik", "10k olma, 20k banan")
   - "query": Foydalanuvchi statistika yoki hisobot so'rayapti. (Masalan: "bugun qancha ketdi?", "oylik hisobot", "ro'yxat")
   - "command": Oxirgi tranzaksiyani o'chirish yoki tahrirlash. (Masalan: "o'chir", "tuzat", "500 emas 400 edi")

2. MA'LUMOTLAR FORMATI:
   - Agar "transaction":
     [ {{"amount": number, "type": "income"|"expense", "category": string, "date": "YYYY-MM-DD", "note": string|null}}, ... ]
   - Agar "query":
     {{"query_type": "summary"|"category"|"list", "period": "today"|"yesterday"|"week"|"month", "category": string|null}}
   - Agar "command":
     {{"command_type": "delete"|"edit", "new_amount": number|null, "note": string|null}}

KATEGORIYALAR: food, transport, salary, rent, entertainment, health, education, shopping, utilities, transfer, business, other.

SUMMA QOIDASI: "50k" -> 50000, "1 mln" -> 1000000, "o'n ming" -> 10000.

Return ONLY valid JSON:
{{
  "intent": "transaction" | "query" | "command" | "none",
  "data": <mos_keladigan_obyekt_yoki_list>
}}
"""


# ─── Public API (Async) ──────────────────────────────────────────────────

async def transcribe_voice(audio_data: bytes) -> str | None:
    """Transcribe voice audio to text using Gemini multimodal (Async)."""
    try:
        b64_audio = base64.b64encode(audio_data).decode("utf-8")
        client = _get_client()
        
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=audio_data, mime_type="audio/ogg"),
                types.Part.from_text(text=(
                    "Transcribe this voice message EXACTLY as spoken. "
                    "ONLY transcribed text, no labels."
                )),
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
            )
        )
        
        text = response.text or ""
        text = text.strip().strip('"').strip("'")
        if text:
            logger.info(f"Transcribed voice: {text}")
            return text
        return None
    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        return None


async def analyze_message(text: str) -> dict:
    """Unified handler: detects intent and extracts data in a single async AI call."""
    try:
        client = _get_client()
        today_str = date.today().isoformat()
        
        prompt = SYSTEM_PROMPT.format(today=today_str)
        full_content = f'{prompt}\n\nFoydalanuvchi xabari: "{text}"'
        
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=full_content,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            )
        )
        
        # Parse JSON from response
        text_resp = response.text.strip()
        result = json.loads(text_resp)
        
        logger.info(f"Analyzed intent: {result.get('intent')} for input: '{text}'")
        return result
        
    except Exception as e:
        logger.error(f"Unified AI analysis error: {e}")
        return {"intent": "none", "data": None}


# ─── Deprecated / Special Helpers ───────────────────────────────────────
# Keep these as wrappers if needed for backward compatibility during transition

async def parse_transaction(text: str) -> list[dict]:
    res = await analyze_message(text)
    if res["intent"] == "transaction":
        return res["data"] if isinstance(res["data"], list) else [res["data"]]
    return []

async def parse_query(text: str) -> dict | None:
    res = await analyze_message(text)
    if res["intent"] == "query":
        return res["data"]
    return None

async def parse_command(text: str) -> dict | None:
    res = await analyze_message(text)
    if res["intent"] == "command":
        return res["data"]
    return None
