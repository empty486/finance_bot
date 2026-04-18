"""Telegram bot setup — dispatcher, routers, and middleware registration."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.bot.middlewares.db import DbSessionMiddleware
from app.bot.handlers import start, transaction
from app.bot.handlers.history import router as history_router
from app.services.analytics_service import get_summary, get_monthly_report, generate_insight

logger = logging.getLogger(__name__)


def format_amount(amount: float) -> str:
    """Format amount with thousands separators."""
    return f"{amount:,.0f}" if amount else "0"


# Stats command router (needs to be registered before the catch-all text handler)
stats_router = Router()


@stats_router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    """Handle /stats — today's summary."""
    user_id = message.from_user.id
    summary = await get_summary(session, user_id, "today")

    response = (
        f"📊 <b>Bugungi statistika</b>\n\n"
        f"📈 Daromad: <b>{format_amount(summary['total_income'])} so'm</b>\n"
        f"📉 Xarajat: <b>{format_amount(summary['total_expense'])} so'm</b>\n"
        f"💰 Balans: <b>{format_amount(summary['balance'])} so'm</b>\n"
        f"🔢 Tranzaksiyalar: <b>{summary['transaction_count']}</b>"
    )

    insight = await generate_insight(session, user_id)
    if insight:
        response += f"\n\n{insight}"

    await message.answer(response, parse_mode="HTML")


@stats_router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession) -> None:
    """Handle /week — weekly summary."""
    user_id = message.from_user.id
    summary = await get_summary(session, user_id, "week")

    response = (
        f"📊 <b>Haftalik statistika</b>\n\n"
        f"📈 Daromad: <b>{format_amount(summary['total_income'])} so'm</b>\n"
        f"📉 Xarajat: <b>{format_amount(summary['total_expense'])} so'm</b>\n"
        f"💰 Balans: <b>{format_amount(summary['balance'])} so'm</b>\n"
        f"🔢 Tranzaksiyalar: <b>{summary['transaction_count']}</b>"
    )

    insight = await generate_insight(session, user_id)
    if insight:
        response += f"\n\n{insight}"

    await message.answer(response, parse_mode="HTML")


@stats_router.message(Command("month"))
async def cmd_month(message: Message, session: AsyncSession) -> None:
    """Handle /month — detailed monthly report."""
    user_id = message.from_user.id
    report = await get_monthly_report(session, user_id)

    summary = report["summary"]
    response = (
        f"📊 <b>Oylik hisobot</b>\n\n"
        f"📈 Daromad: <b>{format_amount(summary['total_income'])} so'm</b>\n"
        f"📉 Xarajat: <b>{format_amount(summary['total_expense'])} so'm</b>\n"
        f"💰 Balans: <b>{format_amount(summary['balance'])} so'm</b>\n"
        f"🔢 Tranzaksiyalar: <b>{summary['transaction_count']}</b>\n\n"
        f"📊 Kunlik o'rtacha xarajat: <b>{format_amount(report['daily_avg_expense'])} so'm</b>\n"
        f"📊 Kunlik o'rtacha daromad: <b>{format_amount(report['daily_avg_income'])} so'm</b>"
    )

    # Add top expense categories
    if report["expense_categories"]:
        response += "\n\n🏷 <b>Eng katta xarajat kategoriyalari:</b>"
        for item in report["expense_categories"][:5]:
            response += (
                f"\n  • {item['category']}: {format_amount(item['total'])} so'm "
                f"({item['percentage']}%)"
            )

    if report["insight"]:
        response += f"\n\n{report['insight']}"

    await message.answer(response, parse_mode="HTML")


from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

def setup_bot() -> tuple:
    """Configure and return the bot and dispatcher.

    Returns:
        (bot, dispatcher) tuple
    """
    # Create bot with default properties and 60s timeout for stability
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register middlewares for both messages and callback queries
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # Register routers (ORDER MATTERS — command routers first, then catch-all)
    dp.include_router(start.router)
    dp.include_router(stats_router)
    dp.include_router(history_router)
    dp.include_router(transaction.router)

    logger.info("Bot configured with all handlers and middleware")
    return bot, dp

