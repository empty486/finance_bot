"""Query handler — responds to statistics and analytics questions."""

import logging

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import (
    get_summary,
    get_category_breakdown,
    generate_insight,
)
from app.services.transaction_service import get_transactions_by_period

logger = logging.getLogger(__name__)


def format_amount(amount: float) -> str:
    """Format amount with thousands separators."""
    if amount == 0:
        return "0"
    return f"{amount:,.0f}"


async def handle_query(
    message: Message,
    session: AsyncSession,
    query: dict,
) -> None:
    """Handle a statistics/analytics query from the user."""
    try:
        user_id = message.from_user.id
        query_type = query.get("query_type", "summary")
        period = query.get("period", "today")
        category_filter = query.get("category")

        period_labels = {
            "today": "Bugun",
            "yesterday": "Kecha",
            "week": "Bu hafta",
            "month": "Bu oy",
        }
        period_label = period_labels.get(period, period)

        if query_type == "summary":
            summary = await get_summary(
                session, user_id, period, category=category_filter
            )

            balance_emoji = "🟢" if summary["balance"] >= 0 else "🔴"

            response = (
                f"📊 <b>{period_label} — Moliyaviy hisobot</b>\n"
                f"{'━' * 28}\n\n"
                f"📈 Daromad:  <b>{format_amount(summary['total_income'])} so'm</b>\n"
                f"📉 Xarajat:  <b>{format_amount(summary['total_expense'])} so'm</b>\n"
                f"{balance_emoji} Balans:   <b>{format_amount(summary['balance'])} so'm</b>\n"
                f"🔢 Tranzaksiyalar: <b>{summary['transaction_count']}</b>"
            )

            # Add insight if available
            insight = await generate_insight(session, user_id)
            if insight:
                response += f"\n\n{insight}"

            # Add category breakdown for this period
            breakdown = await get_category_breakdown(
                session, user_id, period, type_filter="expense"
            )
            if breakdown:
                response += f"\n\n🏷 <b>Xarajat kategoriyalari:</b>"
                for item in breakdown[:5]:
                    bar_len = max(1, int(item["percentage"] / 5))
                    bar = "█" * bar_len + "░" * (20 - bar_len)
                    response += (
                        f"\n  {item['category']}: "
                        f"{format_amount(item['total'])} so'm "
                        f"({item['percentage']}%)"
                    )

            await message.answer(response, parse_mode="HTML")

        elif query_type == "category":
            breakdown = await get_category_breakdown(
                session, user_id, period, type_filter="expense"
            )

            if not breakdown:
                await message.answer(
                    f"📊 {period_label} uchun kategoriya ma'lumotlari topilmadi.",
                    parse_mode="HTML",
                )
                return

            lines = [
                f"📊 <b>{period_label} — Kategoriyalar bo'yicha xarajat</b>\n"
                f"{'━' * 28}\n"
            ]
            for item in breakdown:
                bar_len = max(1, int(item["percentage"] / 5))
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(
                    f"🏷 <b>{item['category']}</b>\n"
                    f"   {bar} {item['percentage']}%\n"
                    f"   {format_amount(item['total'])} so'm ({item['count']} ta)\n"
                )

            await message.answer("\n".join(lines), parse_mode="HTML")

        elif query_type == "list":
            transactions = await get_transactions_by_period(
                session, user_id, period, category_filter=category_filter
            )

            if not transactions:
                await message.answer(
                    f"📋 {period_label} uchun tranzaksiyalar topilmadi.",
                    parse_mode="HTML",
                )
                return

            # Calculate totals
            total_income = sum(float(tx.amount) for tx in transactions if tx.type == "income")
            total_expense = sum(float(tx.amount) for tx in transactions if tx.type == "expense")

            lines = [
                f"📋 <b>{period_label} — Tranzaksiyalar ro'yxati</b>\n"
                f"{'━' * 28}\n"
                f"📈 Jami kirim: {format_amount(total_income)} so'm\n"
                f"📉 Jami chiqim: {format_amount(total_expense)} so'm\n"
                f"{'━' * 28}\n"
            ]
            for i, tx in enumerate(transactions[:20], 1):
                emoji = "📈" if tx.type == "income" else "📉"
                lines.append(
                    f"{i}. {emoji} <b>{format_amount(float(tx.amount))}</b> so'm — "
                    f"{tx.category} ({tx.date.strftime('%d.%m')})"
                )

            if len(transactions) > 20:
                lines.append(f"\n... va yana {len(transactions) - 20} ta")

            await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.error(f"Query handler error: {e}")
        await message.answer(
            "❌ Statistikani ko'rsatishda xatolik yuz berdi.\n"
            "Iltimos, qayta urinib ko'ring.",
            parse_mode="HTML",
        )
