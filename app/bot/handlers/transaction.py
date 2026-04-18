"""Transaction handler — parses text & voice messages, saves transactions, shows stats."""

from __future__ import annotations

import io
import logging
from datetime import date

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.parser import analyze_message, transcribe_voice
from app.services.transaction_service import create_transaction
from app.services.category_service import normalize_category, get_or_create_category
from app.services.analytics_service import get_summary

logger = logging.getLogger(__name__)

router = Router()


def format_amount(amount: float) -> str:
    """Format amount with thousands separators."""
    if amount == 0:
        return "0"
    return f"{amount:,.0f}"


async def _build_mini_stats(session: AsyncSession, user_id: int) -> str:
    """Build a mini summary block for today, this week, and this month."""
    today = await get_summary(session, user_id, "today")
    week = await get_summary(session, user_id, "week")
    month = await get_summary(session, user_id, "month")

    return (
        f"\n{'━' * 28}\n"
        f"📊 <b>Qisqacha statistika</b>\n\n"
        f"📅 <b>Bugun:</b>\n"
        f"   📈 {format_amount(today['total_income'])} so'm"
        f" │ 📉 {format_amount(today['total_expense'])} so'm"
        f" │ 💰 {format_amount(today['balance'])} so'm\n\n"
        f"📅 <b>Bu hafta:</b>\n"
        f"   📈 {format_amount(week['total_income'])} so'm"
        f" │ 📉 {format_amount(week['total_expense'])} so'm"
        f" │ 💰 {format_amount(week['balance'])} so'm\n\n"
        f"📅 <b>Bu oy:</b>\n"
        f"   📈 {format_amount(month['total_income'])} so'm"
        f" │ 📉 {format_amount(month['total_expense'])} so'm"
        f" │ 💰 {format_amount(month['balance'])} so'm"
    )



async def _process_and_save(
    message: Message,
    session: AsyncSession,
    parsed_items: list[dict],
    user_id: int,
) -> None:
    """Validate parsed data, save multiple transactions, and respond with stats."""

    if not parsed_items:
        await message.answer(
            "❓ <b>Summani aniqlab bo'lmadi.</b>\n"
            "Iltimos, summani kiriting.\n\n"
            "Masalan: <code>500000</code> yoki <code>500 ming</code>",
            parse_mode="HTML",
        )
        return

    saved_count = 0
    tx_lines = []

    for parsed in parsed_items:
        amount = parsed.get("amount")
        if not amount or amount <= 0:
            continue

        category = parsed.get("category") or "other"
        tx_type = parsed.get("type", "expense")
        if tx_type not in ("income", "expense"):
            tx_type = "expense"

        normalized_category = normalize_category(category)
        tx_date_str = parsed.get("date", date.today().isoformat())

        try:
            tx_date = date.fromisoformat(tx_date_str)
        except (ValueError, TypeError):
            tx_date = date.today()

        note = parsed.get("note")

        # Save
        await get_or_create_category(session, user_id, normalized_category, tx_type)
        await create_transaction(
            session=session,
            user_id=user_id,
            amount=amount,
            type_=tx_type,
            category=normalized_category,
            tx_date=tx_date,
            note=note,
        )
        
        saved_count += 1
        
        # Build line for summary
        type_emoji = "📈" if tx_type == "income" else "📉"
        type_label = "KIRIM" if tx_type == "income" else "CHIQIM"
        formatted_amount = format_amount(amount)
        line = f"✅ {type_emoji} <b>{formatted_amount} so'm</b> — {normalized_category}"
        if note:
            line += f" (<i>{note}</i>)"
        tx_lines.append(line)

    if saved_count == 0:
        await message.answer(
            "❌ Tranzaksiya ma'lumotlarini aniqlab bo'lmadi.",
            parse_mode="HTML",
        )
        return

    # Build response with summary and mini stats
    header = f"✅ <b>{saved_count} ta tranzaksiya saqlandi!</b>\n\n"
    response = header + "\n".join(tx_lines)
    response += await _build_mini_stats(session, user_id)

    await message.answer(response, parse_mode="HTML")


async def _route_text(
    text: str,
    message: Message,
    session: AsyncSession,
    user_id: int,
) -> None:
    """Route text through unified AI analysis pipeline."""

    # Unified analysis (detects intent and extracts data in one call)
    analysis = await analyze_message(text)
    intent = analysis.get("intent")
    data = analysis.get("data")

    # 1. Handle command (edit/delete)
    if intent == "command" and data:
        from app.bot.handlers.manage import handle_edit_delete
        await handle_edit_delete(message, session, data)
        return

    # 2. Handle query (statistics)
    if intent == "query" and data:
        from app.bot.handlers.query import handle_query
        await handle_query(message, session, data)
        return

    # 3. Handle transaction
    if intent == "transaction" and data:
        parsed_list = data if isinstance(data, list) else [data]
        await _process_and_save(message, session, parsed_list, user_id)
        return

    # 4. Fallback if not understood
    if not intent or intent == "none":
        await message.answer(
            "❌ Kechirasiz, bu xabarni tushunolmadim.\n"
            "Iltimos, tranzaksiya ma'lumotlarini qayta yozing.\n\n"
            "Masalan: <code>50k ovqatga sarfladim</code>",
            parse_mode="HTML",
        )


# ─── Text Message Handler ───────────────────────────────────────────────

@router.message(F.text)
async def handle_message(message: Message, session: AsyncSession) -> None:
    """Main text message handler."""
    text = message.text.strip()
    user_id = message.from_user.id

    if not text or text.startswith("/"):
        return

    await _route_text(text, message, session, user_id)


# ─── Voice Message Handler ──────────────────────────────────────────────

@router.message(F.voice)
async def handle_voice(message: Message, session: AsyncSession) -> None:
    """Handle voice messages — transcribe and process."""
    user_id = message.from_user.id

    await message.answer("🎤 Ovozli xabar qabul qilindi, matnga o'girilmoqda...")

    try:
        # Download voice file
        bot = message.bot
        file = await bot.get_file(message.voice.file_id)
        voice_data = io.BytesIO()
        await bot.download_file(file.file_path, voice_data)
        audio_bytes = voice_data.getvalue()

        # Transcribe
        text = await transcribe_voice(audio_bytes)

        if not text:
            await message.answer(
                "❌ Ovozli xabarni tushunib bo'lmadi.\n"
                "Iltimos, aniqroq gapiring yoki matn yozing.",
                parse_mode="HTML",
            )
            return

        await message.answer(
            f"📝 <b>Aniqlandi:</b> <i>{text}</i>",
            parse_mode="HTML",
        )

        # Route through the same pipeline as text
        await _route_text(text, message, session, user_id)

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        await message.answer(
            "❌ Ovozli xabarni qayta ishlashda xatolik.\n"
            "Iltimos, matn shaklida yozing.",
            parse_mode="HTML",
        )


# ─── Catch-all ───────────────────────────────────────────────────────────

@router.message()
async def handle_unsupported(message: Message) -> None:
    """Catch-all for unsupported message types."""
    await message.answer(
        "⚠️ <b>Faqat matn va ovozli xabarlar qabul qilinadi!</b>\n\n"
        "Masalan: <code>50k ovqatga sarfladim</code>",
        parse_mode="HTML",
    )
