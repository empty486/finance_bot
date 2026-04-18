"""Transaction history handler — paginated list with inline keyboard (production-ready)."""

import logging
import math

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.transaction_service import get_transactions
from app.services.analytics_service import get_summary

logger = logging.getLogger(__name__)

router = Router()

PAGE_SIZE = 5


def format_amount(amount: float) -> str:
    """Format amount with thousands separators."""
    if amount == 0:
        return "0"
    return f"{amount:,.0f}"


def _build_history_text(
    transactions: list,
    page: int,
    total_pages: int,
    total_count: int,
    summary: dict = None,
) -> str:
    """Build formatted transaction history text for a page."""
    if not transactions:
        return (
            "📋 <b>Tranzaksiyalar tarixi</b>\n\n"
            "Hozircha hech qanday tranzaksiya yo'q.\n\n"
            "💡 Boshlash uchun xabar yozing:\n"
            "<code>50k ovqatga sarfladim</code>"
        )

    lines = [
        f"📋 <b>Tranzaksiyalar tarixi</b>\n"
        f"📄 Sahifa {page}/{total_pages} • Jami: {total_count} ta\n"
    ]

    # Show summary on first page
    if summary and page == 1:
        balance_emoji = "🟢" if summary["balance"] >= 0 else "🔴"
        lines.append(
            f"{'━' * 28}\n"
            f"📈 Kirim: {format_amount(summary['total_income'])} so'm\n"
            f"📉 Chiqim: {format_amount(summary['total_expense'])} so'm\n"
            f"{balance_emoji} Balans: {format_amount(summary['balance'])} so'm\n"
        )

    lines.append(f"{'━' * 28}\n")

    start_num = (page - 1) * PAGE_SIZE + 1

    for i, tx in enumerate(transactions, start_num):
        emoji = "📈" if tx.type == "income" else "📉"
        type_label = "KIRIM" if tx.type == "income" else "CHIQIM"
        tx_date = tx.date.strftime("%d.%m.%Y")
        amount = format_amount(float(tx.amount))

        lines.append(
            f"{emoji} <b>#{i}</b> │ {tx_date}\n"
            f"   💰 <b>{amount} so'm</b> — {type_label}\n"
            f"   🏷 {tx.category}"
        )
        if tx.note:
            lines.append(f"   📝 <i>{tx.note}</i>")
        lines.append(f"{'─' * 28}")

    return "\n".join(lines)


def _build_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Build pagination inline keyboard."""
    if total_pages <= 1:
        return None

    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"history:{page - 1}")
        )

    buttons.append(
        InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="history:noop")
    )

    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"history:{page + 1}")
        )

    nav_buttons = []
    if page > 2:
        nav_buttons.append(
            InlineKeyboardButton(text="⏮ Birinchi", callback_data="history:1")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="Oxirgi ⏭", callback_data=f"history:{total_pages}")
        )

    keyboard = [buttons]
    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(Command("tranzaksiyalar"))
async def cmd_transactions(message: Message, session: AsyncSession) -> None:
    """Handle /tranzaksiyalar — show paginated transaction history."""
    try:
        user_id = message.from_user.id

        all_txs = await get_transactions(session=session, user_id=user_id, limit=500)
        summary = await get_summary(session, user_id, "month")

        total_count = len(all_txs)
        total_pages = max(1, math.ceil(total_count / PAGE_SIZE))

        page_txs = all_txs[:PAGE_SIZE]
        text = _build_history_text(page_txs, 1, total_pages, total_count, summary)
        keyboard = _build_keyboard(1, total_pages)

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Transaction history error: {e}")
        await message.answer(
            "❌ Tranzaksiyalar tarixini ko'rsatishda xatolik.",
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("history:"))
async def handle_pagination(callback: CallbackQuery, session: AsyncSession) -> None:
    """Handle pagination button clicks."""
    if callback.data == "history:noop":
        await callback.answer()
        return

    try:
        page = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xatolik")
        return

    try:
        user_id = callback.from_user.id

        all_txs = await get_transactions(session=session, user_id=user_id, limit=500)
        summary = await get_summary(session, user_id, "month")

        total_count = len(all_txs)
        total_pages = max(1, math.ceil(total_count / PAGE_SIZE))
        page = max(1, min(page, total_pages))

        start = (page - 1) * PAGE_SIZE
        page_txs = all_txs[start:start + PAGE_SIZE]

        text = _build_history_text(page_txs, page, total_pages, total_count, summary)
        keyboard = _build_keyboard(page, total_pages)

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except TelegramBadRequest as e:
        # Message not modified — user clicked same page button
        if "message is not modified" in str(e):
            await callback.answer()
        else:
            logger.error(f"Pagination error: {e}")
            await callback.answer("❌ Xatolik")
    except Exception as e:
        logger.error(f"Pagination error: {e}")
        await callback.answer("❌ Xatolik yuz berdi")
